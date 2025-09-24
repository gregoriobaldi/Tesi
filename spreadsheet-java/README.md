# Spreadsheet Java Application

## Overview
This project is a Java implementation of a spreadsheet application. It provides functionalities for managing data in a tabular format, including formula evaluation, data persistence, and a user interface for interaction.

## Project Structure
The project is organized as follows:

```
spreadsheet-java
├── src
│   ├── main
│   │   ├── java
│   │   │   ├── com
│   │   │   │   └── spreadsheet
│   │   │   │       ├── Engine.java
│   │   │   │       ├── Formula.java
│   │   │   │       ├── Main.java
│   │   │   │       ├── Model.java
│   │   │   │       ├── Storage.java
│   │   │   │       ├── UI.java
│   │   │   │       └── Undo.java
│   ├── test
│   │   ├── java
│   │   │   ├── com
│   │   │   │   └── spreadsheet
│   │   │   │       └── BasicTest.java
├── samples
│   ├── sample_data.csv
│   └── sample_workbook.json
├── pom.xml
└── README.md
```

## Setup Instructions
1. **Clone the Repository**: 
   ```
   git clone <repository-url>
   cd spreadsheet-java
   ```

2. **Build the Project**: 
   Use Maven to build the project:
   ```
   mvn clean install
   ```

3. **Run the Application**: 
   Execute the main class:
   ```
   mvn exec:java -Dexec.mainClass="com.spreadsheet.Main"
   ```

## Usage Guidelines
- Upon running the application, users will be presented with a user interface to input data and formulas.
- Users can manipulate the spreadsheet by adding, editing, and deleting cells.
- The application supports basic formula evaluation, allowing users to perform calculations directly within the spreadsheet.

## Testing
Unit tests are provided in the `src/test/java/com/spreadsheet/BasicTest.java` file. To run the tests, use:
```
mvn test
```

## Dependencies
This project uses Maven for dependency management. The `pom.xml` file contains all necessary dependencies for building and running the application.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.