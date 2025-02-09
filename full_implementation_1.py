import cv2
import numpy as np
import matplotlib.pyplot as plt
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

def preprocess_image(image, logger):
    """Preprocessing to enhance text clarity and make it thinner for OCR."""
    logger.info("Starting image preprocessing.")
    # Convert to grayscale
    gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)

    # Apply noise reduction
    denoised = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)

    # Increase contrast
    pil_img = Image.fromarray(denoised)
    enhancer = ImageEnhance.Contrast(pil_img)
    high_contrast = enhancer.enhance(2.5)
    high_contrast = np.array(high_contrast)

    # Apply adaptive thresholding
    binarized = cv2.adaptiveThreshold(high_contrast, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                      cv2.THRESH_BINARY, 15, 10)
    
    # Thin text using erosion
    kernel = np.ones((1, 1), np.uint8)
    eroded = cv2.erode(binarized, kernel, iterations=2)

    # Sharpening
    blurred = cv2.GaussianBlur(eroded, (5, 5), 0)
    sharpened = cv2.addWeighted(eroded, 1.5, blurred, -0.5, 0)
    
    logger.info("Image preprocessing completed.")
    return Image.fromarray(sharpened)

def correct_spelling(text: str, logger) -> str:
    """Correct spelling errors in a given text using TextBlob."""
    logger.info("Correcting spelling ...")
    corrected_text = str(TextBlob(text).correct())
    return corrected_text

def extract_text_from_pdf(pdf_path: str, output_path: str, logger, queue, basic: bool= False) -> List[str]:
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
                            extracted_text.append(correct_spelling(text, logger))
                return extracted_text
            else:
                logger.info("No text layer found. Extracting text using OCR.")
        images = convert_from_path(pdf_path)
        images = images[:15] #TODO
        reader = easyocr.Reader(['en'])
        total_rows=len(images)
        for i, image in enumerate(images):
            processed_image = preprocess_image(image, logger)
            preprocessed_images.append(processed_image)
            results = reader.readtext(np.array(processed_image))
            page_text = ' '.join([text[1] for text in results])
            extracted_text.append(correct_spelling(page_text, logger))
            progress_percentage = (i + 1) / total_rows * 100
            queue.put(('progress', progress_percentage))
            queue.put(('progress_label', f"{progress_percentage:.2f}% ({i + 1}/{total_rows})"))
        # Save preprocessed images as PDF
        preprocessed_pdf_path = output_path.replace(".txt", "_preprocessed.pdf")
        preprocessed_images[0].save(preprocessed_pdf_path, save_all=True, append_images=preprocessed_images[1:])
        logger.info(f"Preprocessed images saved as PDF: {preprocessed_pdf_path}")
        
        logger.info("Text extraction completed.")
        return extracted_text
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        return []

def extract_text(file_path: str, output_path: str, logger, queue, basic) -> List[str]:
    file_extension = os.path.splitext(file_path)[1].lower()
    logger.info(f"Extracting text from file: {file_path}")
    if file_extension == '.pdf':
        return extract_text_from_pdf(file_path, output_path, logger, queue, basic)
    else:
        logger.warning(f"Unsupported file format: {file_extension}")
        return []

def save_extracted_text(text_list: List[str], output_path: str, logger) -> str:
    if not text_list:
        logger.warning("No text to save!")
        return ""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = f"{output_path}"
    logger.info(f"Saving extracted text to: {file_path}")
    with open(file_path, 'w', encoding='utf-8') as f:
        for idx, text in enumerate(text_list, 1):
            f.write(f"--- Page/Section {idx} ---\n")
            f.write(text.strip())
            f.write('\n\n')
    logger.info(f"Text successfully saved to: {file_path}")
    return file_path

def main(pdf_file, output_path, logger, queue, basic):
    logger.info(f"Starting processing for: {pdf_file}")
    pdf_text = extract_text(pdf_file,output_path, logger, queue, basic)
    if pdf_text:
        save_extracted_text(pdf_text, output_path, logger)
    logger.info("Processing completed.")
