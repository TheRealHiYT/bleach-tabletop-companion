@echo off
echo Installing required Python libraries...

REM Flask for web server
pip install flask

REM Transformers for Hugging Face pipelines
pip install transformers

REM If you're using PyTorch backend for transformers
pip install torch

REM Optionally, install math helpers like numpy (used in many AI models)
pip install numpy

echo.
echo Installation complete!
pause
