import os
import time
import string
import numpy as np
import pandas as pd
from glob import glob
from pandas.core.frame import DataFrame
from movifex.pipelines.visual_features.models.vgg19 import getModelVariables as getVgg19Variables
from movifex.pipelines.visual_features.models.inception3 import getModelVariables as getIncp3Variables

def initMovieFramesFolders(configs: dict):
    """
    Pre-checks the given directory for movie frames and prepares it for further processing

    Parameters
    ----------
    configs: dict
        The configurations dictionary
    
    Returns
    -------
    framesFolders :list
        A list of fetched frames folders
    """
    # Variables
    framesFolders = []
    imageTypes = configs['image_formats']
    movieFramesRootDir, vFeaturesDir = configs['frames_path'], configs['features_path']
    # Check if the given directory exists
    if not os.path.exists(movieFramesRootDir):
        print(f"Input movie frames root directory '{movieFramesRootDir}' does not exist! Exiting ...")
        return False
    print(f"Movie frames will be processed from the root directory '{movieFramesRootDir}' ...")
    # Check if the output directory exists and create it if not
    if not os.path.exists(vFeaturesDir):
        os.mkdir(vFeaturesDir)
        print(f"Output visual features will be saved in '{vFeaturesDir}' ...")
    # Check the supported frame types
    print(f"Processing the input frames directory. Supported frame formats are {imageTypes} ...")
    # Get the list of movie folders in the root directory
    for frameFolder in glob(f'{movieFramesRootDir}/*/'):
        for imageType in imageTypes:
            if glob(f'{frameFolder}*.{imageType}'):
                framesFolders.append(frameFolder)
                break  # Exit inner loop if at least one frame is found in this folder
    # Inform the user about the number of frame folders to process
    if len(framesFolders) == 0:
        print(f"No movie frame folders found in the given directory '{movieFramesRootDir}'! Exiting ...")
        return False
    print(f"Found {len(framesFolders)} folders containing frames to process! (e.g., {framesFolders[0]})\n")
    # Return the list of video files
    return framesFolders

def initFeaturesFolder(framesDir: str, featuresDir: str):
    """
    Pre-checks and generates the output visual features folder

    Parameters
    ----------
    framesDir: str
        The frames folder address to extract visual features from
    featuresDir: str
        The visual features directory to save the extracted features
    
    Returns
    -------
    videoFiles: list
        A list of fetched video files
    """
    # Take the last part of the frames directory
    folderName = os.path.basename(framesDir)
    # Normalizing the frames folder name to assign it to the output feature folder
    folderName = string.capwords(folderName.replace("_", "")).replace(" ", "")
    # Creating output folder
    generatedPath = os.path.join(featuresDir, folderName)
    # Do not re-generate features for movie frames if there is a folder with their normalized name
    if os.path.exists(generatedPath):
        print(
            f'- Skipping {folderName} due to finding an output folder with the same name!')
        return
    else:
        os.mkdir(generatedPath)
        return generatedPath

def featureExtractor(imageFile, model, preProcess, inputSize: int):
    """
    Pre-checks and generates the output visual features folder

    Parameters
    ----------
    framesDir: str
        The frames folder address to extract visual features from
    featuresDir: str
        The visual features directory to save the extracted features
    
    Returns
    -------
    videoFiles: list
        A list of fetched video files
    """
    # Imports
    from tensorflow.keras.preprocessing.image import load_img, img_to_array
    # Variables
    features = None
    try:
        # Extracting the content of the image
        imageContent = load_img(imageFile, target_size=(inputSize, inputSize))
        # Convert the image pixels to a numpy array
        frameData = img_to_array(imageContent)
        frameData = np.expand_dims(frameData, axis=0)
        # Preprocessing
        frameData = preProcess(frameData)
        # Get extracted features
        features = model.predict(frameData)
        # Return the extracted features
        return features
    except Exception as error:
        print(f'- Error while extracting the features of "{imageFile}": {str(error)}')
        return None

def featuresFileCreator(targetPath: str, fileName: str):
    """
    Creates a features file for a given movie ID and file name

    Parameters
    ----------
    targetPath: str
        The target path to save the features
    fileName: str
        The file name to save the features
    
    Returns
    -------
    featuresFilePath: str
        The path of the created features file
    """
    # Create the features file path
    featuresFilePath = f'{targetPath}/{fileName}.json'
    # Create the features file if not exists
    if not os.path.exists(featuresFilePath):
        open(featuresFilePath, 'w+')
    # Return the features file path
    return featuresFilePath

def packetManager(packetIndex: int, dataFrame: DataFrame, framesFolder: str, targetPath: str):
    """
    Manages the contents of a packet and sends a signal whether to reset the counter or not

    Parameters
    ----------
    packetIndex: int
        The index of the packet
    dataFrame: DataFrame
        The data frame to save as a packet
    framesFolder: str
        The movie ID to save the packet for
    targetPath: str
        The target path to save the packet
    """
    try:
        # Format the packet index
        packetIndex = '{0:04d}'.format(packetIndex)
        # Create the packet name
        packetName = f'packet{packetIndex}'
        # Save the packet
        print(f'- Saving "{packetName}" for "{framesFolder}" ...')
        featuresFile = featuresFileCreator(targetPath, packetName)
        dataFrame.to_json(featuresFile, orient="records",
                        double_precision=6)
    except Exception as error:
        print(f'- Error while saving the packet "{packetName}" for "{framesFolder}": {str(error)}')

def modelRunner(model, framesFolder, outputDir, configs: dict):
    """
    Pre-checks the given directory for movie frames and prepares it for further processing

    Parameters
    ----------
    model: Model
        The initialized model for feature extraction
    framesFolder: str
        The frames folder address to extract visual features from
    outputDir: str
        The visual features directory to save the extracted features
    configs: dict
        The configurations dictionary
    
    Returns
    -------
    framesFolders :list
        A list of fetched frames folders
    """
    # Variables
    packetIndex = 1  # Holds the name of the packet, e.g. Packet0001
    packetCounter = 0
    modelInputSize = 0
    modelPreprocess = None
    startTime = time.time()
    packetSize = configs['packet_size']
    imageTypes = configs['image_formats']
    totalFrames = len(os.listdir(framesFolder))
    modelName = configs['feature_extractor_model']
    remainingFrames = len(os.listdir(framesFolder))
    frameFeatureDF = pd.DataFrame(columns=['frameId', 'features'])
    # Prepare the model-specific variables
    if modelName == 'incp3':
        # Load Inception-v3 model variables
        modelInputSize, modelPreprocess = getIncp3Variables()
    elif modelName == 'vgg19':
        # Load VGG-19 model variables
        modelInputSize, modelPreprocess = getVgg19Variables()
    else:
        print(f"Feature extraction model '{modelName}' is not supported! Exiting ...")
        return
    # Loop over the frames in the folder
    for imageType in imageTypes:
        for frameFile in glob(f'{framesFolder}/*.{imageType}'):
            # Variables
            frameFileName = os.path.basename(frameFile)
            framesFolder = os.path.basename(os.path.dirname(frameFile))
            try:
                # Finding frameId by removing .jpg from the name
                frameId = ('frame' + frameFile.rsplit('frame', 1)[1])[:-4]
                # Get the extracted features
                features = featureExtractor(frameFile, model, modelPreprocess, modelInputSize)
                # Check the extracted features
                if features is None:
                    print(f'- No features extracted! Skipping "{frameFileName}" in "{framesFolder}" ...')
                    continue
                # Append rows to dataFrame
                frameFeatureDF = pd.concat([frameFeatureDF, pd.DataFrame([{'frameId': frameId, 'features': features[0]}])],
                                           ignore_index=True)
                packetCounter += 1
                # Reset the counter only if packetCounter reaches the limit (packetSize) and there is no more frames for process
                remainingFrames -= 1
                if ((packetCounter == packetSize) or remainingFrames == 0):
                    # Save dataFrame as packet in a file
                    packetManager(packetIndex, frameFeatureDF,
                                    framesFolder, outputDir)
                    # Clear dataFrame rows
                    frameFeatureDF.drop(frameFeatureDF.index, inplace=True)
                    packetCounter = 0
                    packetIndex += 1
            except Exception as error:
                print(f'- Error while extracting the features of "{frameFileName}" in "{framesFolder}": {str(error)}')
                continue
    # Inform the user about the extraction process
    elapsedTime = '{:.2f}'.format(time.time() - startTime)
    print(
        f'- Extracted {totalFrames} features ({packetIndex-1} packets) of "{framesFolder}" in {elapsedTime} seconds!')