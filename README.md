# Housing Affordability and Commute Tradeoffs

**DAT490 Capstone Project**

## 🎯 Project Overview

Analyzing how commute distance and transit access influence housing affordability using data engineering and machine learning.

### Problem Statement
Quantify the relationship between housing costs, commute time, and public transit accessibility to identify affordability zones and inform policy decisions.

### Data Sources
- **Zillow**: Rental price data
- **Census ACS**: Commute patterns and demographics  
- **OpenStreetMap**: Transit network data

### Methodology
- **Data Pipeline**: Automated ETL with orchestration
- **Regression Analysis**: Multiple regression for affordability prediction
- **Clustering**: K-Means for affordability zone identification
- **Visualization**: Interactive dashboard for insights

## 📁 Project Structure

```
DAT490/
├── data/
│   ├── raw/              # Raw data from sources
│   ├── processed/        # Cleaned and transformed data
│   └── models/           # Trained ML models
├── src/
│   ├── pipelines/        # Data ingestion & transformation
│   ├── models/           # ML models (regression, clustering)
│   ├── dashboard/        # Interactive dashboard
│   └── utils/            # Configuration and utilities
├── notebooks/            # Jupyter notebooks for analysis
├── docker/               # Docker configuration
├── tests/                # Unit tests
├── .env                  # Environment variables (not in git)
├── .gitignore
├── requirements.txt
└── README.md
```

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Git
- Docker (optional)

### Installation

```bash
# Clone repository
git clone https://github.com/PeteVanBenthuysen/DAT490.git
cd DAT490

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

## 📊 Usage

```bash
# Run data pipeline
python -m src.pipelines.ingestion
python -m src.pipelines.transform

# Train models
python -m src.models.regression
python -m src.models.clustering

# Launch dashboard
python -m src.dashboard.app
```

## 🐳 Docker Deployment

```bash
cd docker
docker-compose up --build
```

## 📈 Deliverables

- ✅ City-level affordability map
- ✅ Interactive dashboard
- ✅ Policy recommendations
- ✅ Equity-focused analysis
- ✅ Production-ready data pipeline

## 🤝 Team

DAT490 Capstone Project

## 📝 License

MIT License
