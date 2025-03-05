import cv2
import numpy as np
from pdf2image import convert_from_path
from PIL import Image, ImageEnhance
import easyocr
import PyPDF2
from docx import Document
import os
from typing import List
import fitz  # PyMuPDF for checking if PDF has text layer
import json
from datetime import datetime
from textblob import TextBlob
import logging
import traceback 

def preprocess_image(image, logger):
    """Preprocessing to enhance text clarity and make it thinner for OCR."""
    logger.info("Starting image preprocessing.")
    gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)
    pil_img = Image.fromarray(denoised)
    enhancer = ImageEnhance.Contrast(pil_img)
    high_contrast = enhancer.enhance(2.5)
    high_contrast = np.array(high_contrast)
    binarized = cv2.adaptiveThreshold(high_contrast, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 10)
    kernel = np.ones((1, 1), np.uint8)
    eroded = cv2.erode(binarized, kernel, iterations=50)
    blurred = cv2.GaussianBlur(eroded, (5, 5), 0)
    sharpened = cv2.addWeighted(eroded, 1.5, blurred, -0.5, 0)
    
    logger.info("Image preprocessing completed.")
    return Image.fromarray(sharpened)

def detect_columns(image, logger, headline_height_ratio=0.25, gap_threshold=100):
    """Detects at most two columns in an image while ignoring the headline and removing padding."""
    logger.info("Processing image for column detection.")

    # Step 1: Convert image to grayscale & find non-white areas for padding removal
    gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
    _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

    # Find content bounds (left & right)
    cols = np.where(np.sum(binary, axis=0) > 0)[0]
    if len(cols) == 0:
        logger.info("No content detected, returning original image.")
        return [image]

    left, right = cols[0], cols[-1]
    image = image.crop((left, 0, right, image.height))
    logger.info(f"Padding removed: Cropped width from {left} to {right}")

    width, height = image.size
    headline_height = int(height * headline_height_ratio)

    # Step 2: Detect edges in content area (ignoring headline)
    content_area = image.crop((0, headline_height, width, height))
    gray = cv2.cvtColor(np.array(content_area), cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)

    # Step 3: Detect vertical lines
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=120, minLineLength=100, maxLineGap=10)

    if lines is None:
        logger.info("No columns detected, assuming single column layout.")
        return [image]

    # logger.info("Columns detected.")
    column_positions = []

    # Step 4: Extract vertical line positions
    for line in lines:
        x1, _, x2, _ = line[0]
        column_positions.append(min(x1, x2))  # Store the leftmost x position

    if not column_positions:
        logger.info("No significant column dividers found.")
        return [image]

    # Step 5: Find the best column divider with the largest gap
    column_positions.sort()
    max_gap = 0
    best_divider = None
    prev_x = 0  # Start from the left margin

    for x in column_positions:
        gap = x - prev_x
        if gap > max_gap:
            max_gap = gap
            best_divider = x
        prev_x = x

    if best_divider is None or max_gap < gap_threshold:
        logger.info(f"No valid column dividers found with gap > {gap_threshold}. Returning single column.")
        return [image]

    # logger.info(f"Selected column divider at x={best_divider}, gap={max_gap}")

    # Step 6: Split columns while keeping the headline intact
    left_column = image.crop((0, 0, best_divider, height))
    right_column = image.crop((best_divider + 10, 0, width, height))

    return [left_column, right_column]

def correct_spelling(text: str, logger) -> str:
    """Corrects spelling errors in a given text using TextBlob."""
    logger.info("Correcting spelling...")
    corrected_text = str(TextBlob(text).correct())
    return corrected_text

def extract_text_from_pdf(pdf_path: str, output_path: str, logger, queue, basic: bool = False, spellcheck: bool = False) -> List[str]:
    extracted_text = []
    preprocessed_images = []
    
    try:
        logger.info(f"Processing PDF: {pdf_path}")
        if basic:
            doc = fitz.open(pdf_path)
            has_text = any(page.get_text().strip() for page in doc)
            doc.close()
            
            if has_text:
                logger.info("PDF contains text layer, extracting text.")
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text = page.extract_text()
                        if text.strip():
                            if spellcheck:
                                extracted_text.append(correct_spelling(text, logger))
                            else:
                                extracted_text.append(text)
                return extracted_text
            else:
                logger.info("No text layer found. Extracting text using OCR.")

        images = convert_from_path(pdf_path)
        # images = images[:5]  # Limit to 5 pages for processing
        reader = easyocr.Reader(['en'])
        total_rows = len(images)

        for i, image in enumerate(images):
            processed_image = preprocess_image(image, logger)
            preprocessed_images.append(processed_image)

            # Detect columns and extract text from each
            columns = detect_columns(image, logger)
            page_text = []
            
            for column_img in columns:
                results = reader.readtext(np.array(column_img))
                column_text = ' '.join([text[1] for text in results])
                if spellcheck:
                    page_text.append(correct_spelling(column_text, logger))
                else:
                    page_text.append(column_text)
            
            extracted_text.append("\n".join(page_text))

            progress_percentage = (i + 1) / total_rows * 100
            queue.put(('progress', progress_percentage))
            queue.put(('progress_label', f"{progress_percentage:.2f}% ({i + 1}/{total_rows})"))

        preprocessed_pdf_path = output_path.replace(".txt", "_preprocessed.pdf")
        preprocessed_images[0].save(preprocessed_pdf_path, save_all=True, append_images=preprocessed_images[1:])
        logger.info(f"Preprocessed images saved as PDF: {preprocessed_pdf_path}")
        
        logger.info("Text extraction completed.")
        return extracted_text

    
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}\n{traceback.format_exc()}")
        return []

def extract_text(file_path: str, output_path: str, logger, queue, basic, spellcheck) -> List[str]:
    file_extension = os.path.splitext(file_path)[1].lower()
    logger.info(f"Extracting text from file: {file_path}")
    if file_extension == '.pdf':
        return extract_text_from_pdf(file_path, output_path, logger, queue, basic, spellcheck)
    else:
        logger.warning(f"Unsupported file format: {file_extension}")
        return []

def save_extracted_text(text_list: List[str], output_path: str, logger) -> str:
    if not text_list:
        logger.warning("No text to save!")
        return ""
    
    file_path = f"{output_path}"
    logger.info(f"Saving extracted text to: {file_path}")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        for idx, text in enumerate(text_list, 1):
            f.write(f"--- Page/Section {idx} ---\n")
            f.write(text.strip())
            f.write('\n\n')
    
    logger.info(f"Text successfully saved to: {file_path}")
    return file_path

def main(pdf_file, output_path, logger, queue, basic, spellcheck):
    logger.info(f"Starting processing for: {pdf_file}")
    output_path = f"{output_path}/{os.path.splitext(os.path.basename(pdf_file))[0]}.txt"
    logger.info(f"Output path {output_path}")
    pdf_text = extract_text(pdf_file, output_path, logger, queue, basic, spellcheck)
    if pdf_text:
        save_extracted_text(pdf_text, output_path, logger)
    logger.info("Processing completed.")