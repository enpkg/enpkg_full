#!/bin/bash

# Define the path to the directory containing all your directories
PARENT_DIR="/home/allardpm/ENPKG/data/pf1600/pf1600_reprocess"

# Define the content or the source path of the files you want to copy
CONTENT_OF_TXT_FILE="/home/allardpm/ENPKG/data/pf1600/dump/lcms_method_params_neg.txt"
CONTENT_OF_XML_FILE="/home/allardpm/ENPKG/data/pf1600/dump/lcms_processing_params_neg.xml"

# Loop through all directories within the parent directory
for DIR in ${PARENT_DIR}/*; do
    if [ -d "${DIR}" ]; then # If it's a directory
        # Extract the base name of the current directory
        BASE_NAME=$(basename ${DIR})

        # Construct the file names based on the directory name
        NEW_TXT="${DIR}/neg/${BASE_NAME}_lcms_method_params_neg.txt"
        NEW_XML="${DIR}/neg/${BASE_NAME}_lcms_processing_params_neg.xml"

        # Add content to the new files or copy content from a source file
        # echo "${CONTENT_OF_TXT_FILE}" > ${NEW_TXT}
        # echo "${CONTENT_OF_XML_FILE}" > ${NEW_XML}
        
        # Uncomment the lines below if CONTENT_OF_XXX_FILE variables are paths to source files
        # and you want to copy from them instead of using echo
        cp "${CONTENT_OF_TXT_FILE}" ${NEW_TXT}
        cp "${CONTENT_OF_XML_FILE}" ${NEW_XML}

        # Optional: Output some status messages
        echo "Files added to ${DIR}/pos"
    fi
done

# End of script
