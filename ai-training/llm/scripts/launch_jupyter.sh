#!/bin/bash
# Whis Training Jupyter Launcher

echo "🚀 Starting Whis Cybersecurity LLM Training Environment"
echo "📁 Working directory: /home/jimmie/linkops-industries/SOAR-copilot/training"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "🐍 Activating virtual environment..."
    source venv/bin/activate
fi

# Install requirements if needed
if [ -f "requirements.txt" ]; then
    echo "📦 Installing requirements..."
    pip install -r requirements.txt
fi

# Start Jupyter
echo "📓 Starting Jupyter Notebook..."
cd /home/jimmie/linkops-industries/SOAR-copilot/training
jupyter lab whis_cybersec_finetuning.ipynb --ip=0.0.0.0 --port=8888 --no-browser --allow-root

echo "✅ Jupyter session ended"
