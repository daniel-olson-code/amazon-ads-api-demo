# Amazon Ads API Flask Demo

### Intent

Demonstrate how to interact with Amazon's Ads API using a simple Flask application.

This project is designed to showcase how developers can integrate Amazon's Ads Report API into a web application, making it more interactive and user-friendly. It serves as both a learning tool and a practical example for those looking to work with Amazon's advertising report data programmatically.

The Flask app provides a straightforward UI for interacting with the Report API, allowing users to request advertising reports without needing to write code directly. While this implementation is intended for local use and demonstration purposes, it illustrates the potential for building more complex reporting applications using these technologies.

By creating this project, I aim to:
1. Demonstrate proficiency in Python programming and API integration
2. Showcase specific usage of Amazon's Ads Report API within a web application
3. Provide a practical example of using Flask to create an interactive interface for API interactions
4. Offer a foundation for digital marketers and developers looking to automate and streamline their Amazon Ads reporting processes

This example application focuses on common reporting tasks such as:
- Requesting various types of advertising reports
- Checking report status
- Downloading and displaying report data
- Basic data visualization of report results

While simple in design, this demo illustrates how the Report API can be leveraged to create powerful tools for analyzing and optimizing Amazon advertising campaigns.

---

### WARNING
This application is designed for local use and educational purposes. It should not be deployed to a public server without significant modifications to ensure security and scalability.

---

### Functionality:
* Authenticate with Amazon Ads API
* Retrieve report version 3 data using

The simplicity of this interface combined with the power of Amazon's Ads API opens up possibilities for marketers and developers to automate tasks, analyze data, and manage campaigns more effectively.

---

### Support

If you find this project helpful, consider leaving a star on GitHub.

For those who have benefited from this project or would like to see additional features, please consider supporting:

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://buymeacoffee.com/daniel.olson)

--- 

### Prerequisites
* Python 3.10 or above
* Amazon Ads API credentials

---

### Setup Guide:

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up your Amazon Ads API credentials:
- Create a `.env` file in the root directory of the project
- Add the following lines to the `.env` file, replacing the placeholder values with your actual credentials:
  ```
  AMAZON_ADS_CLIENT_ID=your_client_id_here
  AMAZON_ADS_CLIENT_SECRET=your_client_secret_here
  ```
4. Run the Flask app: `python app.py`
5. Open your browser and navigate to `http://localhost:5000`


