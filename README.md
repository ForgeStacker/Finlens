# FinLens

> Offline, decision-first cloud visibility for non-technical leaders.

FinLens converts complex AWS infrastructure into a clear, interactive report that non-technical leaders can understand without relying on engineers.

No SaaS. No backend dependency. No live dashboards.
Just a portable cloud snapshot that helps people make better decisions.

An open-source, offline cloud infrastructure reporting tool.

Designed to produce deterministic, auditable reports that remain usable long after generation.

📋 **[View Complete Project Overview →](PROJECT_OVERVIEW.md)**

## What FinLens Actually Does

1. You run FinLens locally.
2. It scans your AWS accounts.
3. It generates a self-contained report.
4. The report opens in your browser.
5. You review your infrastructure clearly.

After generation, the report works without internet access.

## Overview Dashboard

![Overview](assets/ResourceOverviewPage.png)

## Service Detail View

![Service Detail](assets/ServiceDetailPage.png)

## Account Sidebar

![Account Sidebar](assets/AccountSideBar.png)

## Region Sidebar

![Region Sidebar](assets/RegionSidebar.png)

## Why FinLens Exists

Cloud consoles are built for engineers.
Cost dashboards show numbers, not decisions.

Non-technical leaders still need to answer:
- What is running?
- What looks wasteful?
- What seems risky?
- What should we review first?

FinLens exists to answer those questions clearly.

## Who FinLens Is For

- Founders
- Product managers
- Operations leaders
- Technical leads who need fast infrastructure clarity

If you are looking for real-time monitoring, alerts, or automated remediation,
FinLens is intentionally not that.

## What FinLens Will NOT Do

FinLens intentionally does not:

- Monitor systems in real time
- Send alerts
- Automatically fix infrastructure
- Require a SaaS backend
- Lock you into a platform

It focuses on one thing only: helping humans make better cloud decisions.

## Quick Start (Docker - Recommended)

1. Configure AWS credentials.
2. Run: `./start-finlens.sh`
3. Browser opens automatically.

Access: http://localhost:5173

> Detailed setup instructions are provided below.

## ✨ Latest Updates (Release 1.0)

### 🎨 **Professional UI Enhancements**
- **Official AWS Icons**: 59+ authentic AWS service icons for professional branding
- **Dark/Light Theme Toggle**: Complete theme switching with system preference support
- **Enhanced Service Names**: Properly formatted names like "Secrets Manager", "Compute Optimizer"
- **DetailSidebar**: New expandable right sidebar for detailed resource information with key-value table layout
- **DataPopover**: Smart popup cards for complex data with portal rendering and theme matching

### 🚀 **Dynamic Features**
- **Runtime Data Discovery**: No static configurations - everything loads dynamically from actual AWS data
- **Smart Filtering**: Dynamic filter options based on real resource states
- **Real-time Resource Counts**: Live data from your actual AWS infrastructure
- **Interactive Data Display**: Click table rows for detailed views, expandable data tags

### 📊 **Comprehensive Service Coverage**
- **75+ AWS Services** across all major categories
- **Multi-Account Support** with environment detection
- **Cross-Region Analysis** with detailed resource inventory
- **Complete Regional Coverage**: All AWS regions supported (us-east-1, ap-south-1 enabled by default)

---

## Detailed Setup and Operations

### Prerequisites

Before using FinLens, ensure you have:

1. **Python 3.8 or higher** installed
2. **AWS Account** with appropriate access
3. **AWS Credentials** configured locally
4. **Docker** (if using containerized mode - recommended)

### Step 1: Configure AWS Credentials ⚠️ REQUIRED

**IMPORTANT**: You **MUST** configure AWS credentials before running FinLens. The application will fail without them.

You need to set up your AWS profile with access keys. There are two ways to do this:

#### Option A: Using AWS CLI (Recommended)

```bash
# Install AWS CLI if not already installed
pip install awscli

# Configure your AWS profile
aws configure --profile your-profile-name

# You'll be prompted to enter:
# AWS Access Key ID: [Enter your access key]
# AWS Secret Access Key: [Enter your secret key]
# Default region name: [Enter region like ap-south-1]
# Default output format: [Press enter or type json]
```

#### Option B: Manual Configuration

Create or edit `~/.aws/credentials` file:

```ini
[your-profile-name]
aws_access_key_id = YOUR_ACCESS_KEY_ID
aws_secret_access_key = YOUR_SECRET_ACCESS_KEY
```

Create or edit `~/.aws/config` file:

```ini
[profile your-profile-name]
region = ap-south-1
output = json
```

**Verify your AWS credentials are configured:**

```bash
# Check if credentials exist
ls -la ~/.aws/

# You should see:
# - credentials (contains access keys)
# - config (contains region and output format)

# Test your AWS credentials work
aws sts get-caller-identity --profile your-profile-name
```

### Step 2: Configure FinLens Profiles

Edit `config/profiles.yaml` to add your AWS profile:

```yaml
profiles:
  - name: your-profile-name  # Must match the profile in ~/.aws/credentials
    environment: production   # or development, staging, etc.
    enabled: true
```

**IMPORTANT**: The profile name in `config/profiles.yaml` must exactly match the profile name in `~/.aws/credentials`.

### Step 3: Clone FinLens

```bash
# Clone the repository
git clone <repository-url>
cd FinLens
```

**Note**: If using Docker (recommended), you can skip dependency installation as Docker handles everything automatically.

### Step 4: Run FinLens

**Option A: Docker (Recommended) - One Command Setup**

The easiest way to run FinLens is using Docker. The script will:
- ✅ Automatically check AWS credentials
- ✅ Verify profile configuration
- ✅ Build and start all services
- ✅ Wait for data collection to complete
- ✅ Auto-open browser when ready

```bash
# Simply run the start script
./start-finlens.sh

# The script will:
# 1. Verify AWS credentials are configured in ~/.aws/
# 2. Check profiles.yaml matches your AWS profiles
# 3. Build Docker containers
# 4. Collect AWS data
# 5. Start frontend
# 6. Open browser automatically
```

**Access Your Dashboard**: http://localhost:5173

**Docker Commands**:
```bash
# View logs
docker compose logs -f

# Restart containers (if you updated AWS credentials)
docker compose restart

# Stop everything
docker compose down

# Rebuild from scratch
docker compose down && ./start-finlens.sh
```

**Option B: Python Direct Run (Advanced)**

**Prerequisites**: You need to install dependencies manually for this option:
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

**Run the application**:
```bash
# Run complete scan and auto-launch dashboard
python finlens.py

# This will:
# - Scan all configured AWS accounts and regions
# - Generate comprehensive resource inventory 
# - Automatically launch the web dashboard
# - Display results at http://localhost:8084
```

**Option C: Manual Launch (Advanced)**

**Prerequisites**: Same dependency installation as Option B above.

**Run the application**:
```bash
# Start API server (Terminal 1)
python frontend/api_server.py

# Start frontend dashboard (Terminal 2)  
cd frontend
npm run dev
```

---

## 🔧 Troubleshooting

### AWS Credentials Issues

**Problem**: "The config profile (your-profile) could not be found"

**Solution**:
1. Verify credentials exist: `ls -la ~/.aws/`
2. Check profile name: `cat ~/.aws/credentials`
3. Test credentials: `aws sts get-caller-identity --profile your-profile`
4. Ensure `config/profiles.yaml` uses the exact same profile name
5. If using Docker, restart containers: `docker compose restart`

**Problem**: Empty data folder or no resources found

**Solution**:
1. AWS credentials might be configured after containers started
2. Run: `docker compose restart` to pick up new credentials
3. Or rebuild: `docker compose down && ./start-finlens.sh`

### Docker Issues

**Problem**: Permission denied accessing Docker

**Solution**: Add your user to docker group: `sudo usermod -aG docker $USER` then logout/login

**Problem**: Containers not picking up code changes

**Solution**: Rebuild without cache: `docker compose down && docker compose build --no-cache`

---

## 🎯 Key Features

### 🏢 **Multi-Account Management**
- Support for multiple AWS profiles and accounts
- Automatic environment detection (Production, Development, Staging)
- Cross-account resource comparison and analysis

### 🌍 **Regional Coverage**
- Comprehensive scanning across all AWS regions
- Regional resource distribution analysis
- Support for region-specific services and limitations

### 📋 **Service Categories**
- **Compute**: EC2, EKS, Lambda, ECS, Elastic Beanstalk
- **Database**: RDS, DynamoDB, ElastiCache, Redshift, DocumentDB  
- **Storage**: S3, EBS, EFS, Storage Gateway
- **Networking**: VPC, CloudFront, Route 53, Load Balancers
- **Security**: IAM, KMS, Secrets Manager, GuardDuty, Inspector
- **Management**: CloudTrail, CloudWatch, Config, Systems Manager
- **Cost Management**: Cost Explorer, Budgets, Reserved Instances
- **AI/ML**: SageMaker, Comprehend, Rekognition, Textract
- **DevOps**: CodeBuild, CodeDeploy, CodePipeline, CloudFormation
- **And 40+ more services...**

### 🎨 **Modern Dashboard**
- **Professional Design**: Dark/light theme with AWS branding
- **Official Icons**: Authentic AWS service icons throughout
- **Smart Filtering**: Dynamic filters based on actual data
- **Responsive Layout**: Works perfectly on desktop, tablet, and mobile
- **Real-time Data**: Live resource counts and status indicators
- **Interactive Interface**: 
  - DetailSidebar for comprehensive resource details
  - DataPopover for expandable data visualization
  - Click-to-expand functionality for complex data structures

### 📊 **Data Intelligence**
- **Dynamic Discovery**: No hardcoded configurations
- **Smart Categorization**: Services grouped logically
- **Resource Relationships**: Understanding dependencies and connections
- **Cost Insights**: Resource cost estimation and optimization hints
- **Complete Regional Coverage**: Support for all AWS regions with easy configuration

---

## ⚙️ Configuration

Edit the configuration files in the `config/` folder to customize your scanning:

#### 3.1 Configure Profiles (`config/profiles.yaml`)

```yaml
profiles:
  - name: your-profile-name        # Must match your AWS profile name
    description: My AWS Account
    accounts:
      - name: "Production"
        id: "123456789012"
      - name: "Development"
        id: "987654321098"
    enabled: true
  
  - name: another-profile          # Add more profiles if needed
    description: Production Account
    enabled: true
```

#### 3.2 Configure Regions (`config/regions.yaml`)

```yaml
include:
  - us-east-1       # US East (N. Virginia) - Default enabled
  - ap-south-1      # Asia Pacific (Mumbai) - Default enabled
  
  # Uncomment additional regions as needed:
  # - us-west-2     # US West (Oregon)
  # - eu-west-1     # Europe (Ireland)
  # - ap-southeast-1 # Asia Pacific (Singapore)
  # And 20+ more regions available...

exclude:
  # - eu-north-1    # Optional: regions to exclude
```

#### 3.3 Configure Services (`config/services.yaml`)

```yaml
mode: include  # Use 'include' to scan only listed services

list:
  - ec2          # EC2 instances
  - vpc          # VPC resources
  # - s3         # Uncomment to add more services
  # - lambda
  # - rds
```

### Step 4: Run FinLens Scan

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run the scan
python finlens.py
```

That's it! FinLens will:
- Automatically read all profiles from `config/profiles.yaml`
- Scan only the included regions from `config/regions.yaml`
- Collect data for included services from `config/services.yaml`
- Generate JSON files in `data/<profile-name>/services/` directory

### Output Location

Scan results are saved in:
```
data/
├── profile-1/
│   └── services/
│       ├── ec2.json
│       ├── vpc.json
│       ├── s3.json
│       └── lambda.json
├── profile-2/
│   └── services/
│       ├── eks.json
│       ├── rds.json
│       └── cloudfront.json
```

---

## 🚀 Release 1.0 Highlights

### Enhanced User Experience
- **Professional Branding**: Complete integration of official AWS service icons (59+ services)
- **Theme Flexibility**: Dark/light theme toggle with system preference detection
- **Smart Navigation**: Improved service name formatting with proper spacing ("Secrets Manager" style)
- **Interactive Data Visualization**: DetailSidebar and DataPopover components for enhanced data exploration

### Dynamic Intelligence  
- **Runtime Discovery**: All data loading is dynamic - no static configurations
- **Smart Filtering**: Filter options automatically generated from actual resource data
- **Real-time Insights**: Live resource counts and status indicators
- **Complete Regional Support**: All AWS regions configured with us-east-1 and ap-south-1 as defaults

### Technical Improvements
- **Modern Frontend**: React + TypeScript with Vite for optimal development experience
- **Component Architecture**: Reusable components with proper separation of concerns
- **Performance**: Optimized data loading and responsive UI design
- **Enhanced Interactivity**: Click-to-expand functionality and detailed resource views

---

## 📚 Documentation

- **[Project Overview](PROJECT_OVERVIEW.md)** - Complete project philosophy, goals, and development approach
- **[Business Requirements Document](BRD%20—%20Business%20Requirements%20Document.md)** - Detailed business requirements and scope
- **[Functional Requirements Document](FRD%20—%20Functional%20Requirements%20Document.md)** - Technical specifications and features
- **[System Architecture Document](System%20Architecture%20Document%20(SAD).md)** - Architecture design and implementation details
- **[Data Contract Document](Data%20Contract%20Document.md)** - Data structures and contracts
- **[Non-Functional Requirements](NFR%20—%20Non-Functional%20Requirements%20Document.md)** - Performance, security, and quality requirements

---

## 🤝 Contributing

1. Read the [Project Overview](PROJECT_OVERVIEW.md) to understand our philosophy
2. Check existing documentation for context
3. Submit issues for bugs or feature requests
4. Follow the development approach outlined in our planning documents

---

## 📞 Support

For questions or issues:
1. Check the documentation files listed above
2. Review the troubleshooting section in this README
3. Submit an issue with detailed information about your setup and the problem

---

**FinLens is built to last, be trusted, and help people think clearly about complex systems.**
