# Enrollware Order Automation

Automates filtering and processing TC Product Orders in Enrollware, updating them on ecard.hearts.org, and sending confirmation emails. Streamlines repetitive workflows for efficiency.

## Features

- **Secure Authentication:** Credentials loaded from environment variables
- **Intelligent Filtering:** Excludes orders with "redcross" or "complete" status
- **Automated Processing:** Processes eligible orders on ecard.hearts.org
- **Status Updates:** Marks orders as "complete" in Enrollware
- **Email Confirmation:** Sends confirmation emails after processing

## How It Works

1. **Login:** Reads credentials from `.env` and authenticates with Enrollware
2. **Navigate:** Opens TC Product Order page
3. **Filter:** Excludes orders with "redcross" or "complete" status
4. **Process:** Processes remaining orders on ecard.hearts.org
5. **Finalize:** Updates status and sends confirmation email

## Prerequisites

- Python 3.12+
- Chrome browser
- Active Enrollware and eCard accounts

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/muhammadhassan1214/enrollware_automation.git
   cd enrollware_order_automation
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize Chrome browser profile:**
   ```bash
   cd Utils
   python init_browser.py
   ```
   - A Chrome window will open. Log in to both Enrollware and eCard sites, then close the browser.

## Configuration

1. **Create or Edit `.env` file in the project root:**
   ```
   ENROLLWARE_USERNAME="your_enrollware_username"
   ENROLLWARE_PASSWORD="your_enrollware_password"
   ATLAS_USERNAME="your_atlas_username_or_email"
   ATLAS_PASSWORD="your_atlas_password"
   ```

## Customization

- **Course Management:**  
  Edit `course.py` to modify available courses IDs and their corresponding eCard names.

## Usage

Run the automation script:
```bash
python main.py
```
