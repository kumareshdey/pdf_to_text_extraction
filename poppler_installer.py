import os
import urllib.request
import zipfile
import subprocess
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def is_textblob_installed(logger):
    """Check if TextBlob is installed"""
    try:
        import textblob
        from textblob import TextBlob
        logger.info("TextBlob is already installed.")
        return True
    except ImportError:
        logger.info("TextBlob is not installed.")
        return False

def install_textblob(logger):
    """Install TextBlob and its corpora"""
    logger.info("Installing TextBlob...")
    subprocess.run([sys.executable, "-m", "pip", "install", "textblob"], check=True)
    
    logger.info("Downloading TextBlob corpora...")
    subprocess.run([sys.executable, "-m", "textblob.download_corpora"], check=True)
    
    logger.info("TextBlob installation and corpora download complete!")

def is_corpora_installed(logger):
    """Check if TextBlob corpora (wordlist) is installed"""
    textblob_data_path = os.path.expanduser("~/.textblob")
    corpora_path = os.path.join(textblob_data_path, "en")
    installed = os.path.exists(corpora_path)

    if installed:
        logger.info("TextBlob corpora is already installed.")
    else:
        logger.info("TextBlob corpora is missing.")
    
    return installed

def install_textblob_corpora(logger):
    """Download TextBlob corpora manually (if needed)"""
    corpora_url = "https://raw.githubusercontent.com/sloria/TextBlob/master/textblob/en/en-GB"
    textblob_data_path = os.path.expanduser("~/.textblob/en")

    os.makedirs(textblob_data_path, exist_ok=True)

    logger.info("Downloading TextBlob corpus manually...")
    urllib.request.urlretrieve(corpora_url, os.path.join(textblob_data_path, "en-GB"))

    logger.info("TextBlob corpus installed successfully!")

def add_textblob_to_path(logger):
    """Ensure TextBlob's corpora path is in the environment"""
    textblob_data_path = os.path.expanduser("~/.textblob")
    os.environ["TEXTBLOB_DATA"] = textblob_data_path
    logger.info(f"TextBlob data path set: {textblob_data_path}")

def is_poppler_installed(logger):
    """Check if Poppler is already installed and available in PATH"""
    try:
        subprocess.run(["pdftoppm", "-v"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        logger.info("Poppler is already installed.")
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        logger.info("Poppler is not installed.")
        return False

def install_poppler(logger):
    """Download and install Poppler"""
    poppler_url = "https://github.com/oschwartz10612/poppler-windows/releases/download/v24.08.0-0/Release-24.08.0-0.zip"
    poppler_zip = "poppler.zip"
    poppler_dir = os.path.join(os.getcwd(), "poppler")

    # Step 1: Download Poppler
    logger.info("Downloading Poppler...")
    urllib.request.urlretrieve(poppler_url, poppler_zip)

    # Step 2: Extract the zip file
    logger.info("Extracting Poppler...")
    with zipfile.ZipFile(poppler_zip, 'r') as zip_ref:
        zip_ref.extractall(poppler_dir)

    # Step 3: Find the extracted Poppler bin directory
    extracted_folder = next(os.scandir(poppler_dir)).path
    bin_path = os.path.join(extracted_folder, "Library", "bin")

    # Step 4: Add to system PATH (for the current session)
    os.environ["PATH"] += os.pathsep + bin_path

    # Step 5: Add permanently to PATH
    add_to_path(bin_path, logger)

    # Cleanup
    os.remove(poppler_zip)
    logger.info("Poppler installed successfully!")

def add_to_path(bin_path, logger):
    """Adds the Poppler bin folder to system PATH permanently"""
    logger.info(f"Adding Poppler to PATH: {bin_path}")

    # Get the current system PATH
    current_path = os.environ["PATH"]

    # Check if already in PATH
    if bin_path in current_path:
        logger.info("Poppler is already in the system PATH.")
        return

    # Add it permanently
    if sys.platform == "win32":
        subprocess.run(f'setx PATH "{current_path};{bin_path}"', shell=True)
        logger.info("Poppler path added permanently! Restart your terminal to apply changes.")

def decider(logger):
    """Main function to install Poppler and TextBlob if needed"""
    if not is_poppler_installed(logger):
        install_poppler(logger)
    else:
        logger.info("Poppler is already installed. No need to install again.")

    # if not is_textblob_installed(logger):
    #     install_textblob(logger)

    # if not is_corpora_installed(logger):
    #     install_textblob_corpora(logger)
    
    # add_textblob_to_path(logger)
    logger.info("TextBlob is ready to use!")

# Run the setup
if __name__ == "__main__":
    import textblob