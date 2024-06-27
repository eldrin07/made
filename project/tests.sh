

# Base directory
BASE_DIR="$HOME/made"

# Run the data pipeline
python3 "$BASE_DIR/project/pipeline.py"

# Test the expected output file
OUTPUT_FILE1="$BASE_DIR/data/cleaned_world_bank_data.csv"

# Check if the output file exists
if [ -f "$OUTPUT_FILE1" ]; then
    echo "Test passed: Output file $OUTPUT_FILE1 exists."
else
    echo "Test failed: Output file $OUTPUT_FILE1 does not exist."
    exit 1
fi

OUTPUT_FILE2="$BASE_DIR/data/cleaned_global_carbon_data.csv"

# Check if the output file exists
if [ -f "$OUTPUT_FILE2" ]; then
    echo "Test passed: Output file $OUTPUT_FILE2 exists."
else
    echo "Test failed: Output file $OUTPUT_FILE2 does not exist."
    exit 1
fi

exit 0
