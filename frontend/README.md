# FinLens - Cloud Infrastructure Scanner

FinLens is a comprehensive AWS cloud infrastructure scanning and analysis tool that provides detailed insights into your cloud resources across multiple accounts and regions.

## Features

- **Multi-Account Support**: Scan multiple AWS accounts from a single interface
- **Regional Analysis**: Comprehensive coverage across all AWS regions
- **Service Discovery**: Automated discovery and analysis of 75+ AWS services
- **Resource Inventory**: Detailed inventory of all cloud resources
- **Cost Analysis**: Resource cost estimation and optimization recommendations
- **Professional Dashboard**: Modern, intuitive web interface with dark theme
- **Data Export**: Export capabilities in JSON and CSV formats
- **Real-time Monitoring**: Live status indicators and health checks

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- AWS CLI configured with appropriate credentials
- Valid AWS profiles in `~/.aws/credentials`

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd Finlens
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```

### Usage

#### Backend Scanning

Run the FinLens scanner:
```bash
python finlens.py
```

This will:
- Scan all configured AWS accounts and regions
- Generate comprehensive resource inventory
- Save results in JSON format under `data/` directory
- Automatically launch the web dashboard

#### Frontend Dashboard

The web dashboard automatically launches after scanning completes. You can also manually start it:

```bash
cd frontend
npm run dev
```

The dashboard provides:
- **Landing Page**: Overview of all scanned accounts and regions
- **Service Cards**: Interactive cards showing resource counts and status
- **Detailed Views**: Comprehensive tables with filtering and sorting
- **Multi-sidebar Navigation**: Easy switching between accounts and regions

## What technologies are used for this project?

This project is built with:

- Vite
- TypeScript
- React
- shadcn-ui
- Tailwind CSS

## Development

### Frontend Development

The frontend is built with modern web technologies:
- React with TypeScript
- Vite for build tooling
- Tailwind CSS for styling
- Shadcn/ui components
- Dark and light theme support

## License

This project is licensed under the MIT License.
