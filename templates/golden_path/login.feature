Feature: User Authentication on SauceDemo

  Scenario: Successful Login with Valid Credentials
    Given the user is on the SauceDemo login page
    When the user enters the username "standard_user" and the password "secret_sauce"
    And clicks the login button
    Then the user should be redirected to the inventory page
    And should see the products list header "Products"

  Scenario: Failed Login with Invalid Credentials
    Given the user is on the SauceDemo login page
    When the user enters the username "invalid_user" and the password "wrong_password"
    And clicks the login button
    Then the user should see an error message containing "Epic sadface: Username and password do not match any user in this service"
