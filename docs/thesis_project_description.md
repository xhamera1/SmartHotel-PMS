# **Bachelor's Thesis Topic Description**

**Author:** Patryk Chamera

**Topic (PL):** System zarządzania hotelem z inteligentnym silnikiem dynamicznego kształtowania cen  
**Topic (EN):** Hotel Management System with an Intelligent Dynamic Pricing Engine  

## **1. Topic Description**

The aim of this thesis is to design and implement a hotel management system equipped with an intelligent dynamic room pricing mechanism. The system is intended to support hotel owners and managers in making pricing decisions based on the current market situation, the level of interest in the offer, and external factors that may affect demand. A significant element of the project will be the use of machine learning methods to forecast demand changes and automatically adjust prices. Additionally, the system will analyze information about events taking place in the area, allowing it to factor in their potential impact on hotel booking interest. The thesis has a practical character and includes both the creation of a complete solution and its evaluation in terms of performance quality, usability, and reliability.

## **2. Project**

### **2.1 System Architecture**

The system will be built using a microservices architecture. The main application will be responsible for handling reservations, managing rooms, and guest data. The module responsible for pricing will act as an independent component, allowing for its development and testing independently of the rest of the system.

Event data will be retrieved from public services providing event calendars. Next, they will be passed to the Gemini language model via Google AI Studio. The model will assess the potential impact of events on hotel booking interest. The resulting assessment will be used as additional information supporting the pricing process.

### **2.2 Intelligent Dynamic Pricing Engine**

The most important element of the project will be an intelligent pricing engine based on machine learning methods. It is planned to use the Random Forest algorithm to analyze data related to hotel operations and predict optimal room prices. The model will take into account, among other things, the hotel's occupancy level, booking date, day of the week, and an interest indicator derived from the analysis of local events.

To train the model, a synthetic dataset reflecting realistic dependencies found in the hotel industry will be prepared.

### **2.3 Functional Scope of the System**

- **Administrative panel (PMS):** managing rooms, prices, guests, and reservations.
- **Booking module:** presentation of available rooms and current prices for customers.
- **Pricing engine:** automatic price determination and integration with external data sources.
- **Integration with LLM:** event analysis and generation of a potential demand growth indicator.

### **2.4 Testing and Evaluation of the Solution**

Due to experience in the field of Quality Assurance, a significant part of the thesis will be the preparation of an automated testing module. The goal will be to verify the quality and reliability of the entire solution, not just the machine learning model.

Planned activities include:
- automated API tests of individual system services,
- end-to-end (E2E) tests reflecting real user scenarios,
- integration tests of communication between system components,
- load and performance tests of microservices,
- automated test execution in the CI/CD process,
- evaluating the performance quality of the Random Forest model and the impact of data provided by the Gemini language model.

As part of the thesis, an analysis of the impact of event information on the effectiveness of demand forecasting will also be conducted, and the usefulness of utilizing a language model in business decision support systems will be evaluated.

## **3. Technology Stack**

- **Main Backend:** Java (Spring Boot)
- **Dynamic Pricing Microservice:** Python (FastAPI, scikit-learn)
- **Frontend:** React
- **Database:** MySQL or PostgreSQL
- **Event APIs:** Ticketmaster / Eventim / Others
- **LLM:** Google Gemini API (Google AI Studio)
- **Containerization:** Docker
- **CI/CD:** GitHub Actions or GitLab CI
- **Tests:** JUnit, RestAssured, Playwright or Selenium
- **Monitoring and logging:** ELK Stack

## **4. Justification for Using Gemini API**

The project plans to use the Google Gemini API available through Google AI Studio. The service offers a free usage tier sufficient for carrying out the diploma project and conducting a presentation during the defense. The terms of service do not prohibit its use in educational and diploma projects. The analyzed data will concern publicly available information about events, therefore no sensitive data or personal data of hotel guests will be transmitted.
