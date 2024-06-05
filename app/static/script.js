// Set up encryption method
const encrypt = new JSEncrypt();
let has_api_data = false;
let session_id = -1;

// Get the page panels
const panels = [
    "home",
    "settings"
];

// Function to show a specific page
const full_page = document.getElementById("full_panel");
const full_page_width = full_page.offsetWidth;
function show_panel(page) {
    const page_index = panels.indexOf(page);
    full_page.style.transform = `translateX(-${page_index * full_page_width}px)`;
};

function show_home() {
    show_panel("home");
}; show_home();
function show_settings() {
    show_panel("settings");
};

// Function to get the public key to the server
function fetch_public_key() {
    $.post({
        url: "/public-key",
        type: "POST",
        success: function(data) {
            // Set the public key in the encryption
            encrypt.setPublicKey(data.public_key);
            // Set the session id
            session_id = data.session_id;

            // Change some stuff based on if a username is set
            if (data.username != "") {
                has_api_data = true;
                document.getElementById("api_data").style.display = "None";
                document.getElementById("password_header").innerHTML = `Welcome back, ${data.username}!`;
            };
        }
    });
};

// Get the public key from the server
fetch_public_key();

// Enable the password container after a short delay
setTimeout(function() {
   document.getElementById("password_container").classList.toggle("show");
}, 500);

// Get home page elements
const profit_element = document.getElementById("profit_element");
const balance_element = document.getElementById("balance_element");

// Function to get the homepage data
function get_homepage() {
    $.post({
        url: "/homepage-data",
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify({ session_id: session_id }),
        success: function(data) {
            //const markets = data.markets;
            const balance = data.balance;
            const profit = data.profit;
            
            if (profit >= 0) {
                profit_element.innerHTML = `Profit: ${profit}%`;
            } else {
                profit_element.innerHTML = `Loss: ${profit}%`;
            }

            balance_element.innerHTML = `Balance: €${balance}`;
        },
        error: post_error
    });
};

// Get password elements
const password_input = document.getElementById("password_input");
const password_message = document.getElementById("password_message");

// Variable to store hash of password globally
let password_hash = "";

// Function to do a first time login
function first_time_login() {
    // Get entered password
    const password = password_input.value;

    // Set message text to empty
    password_message.innerHTML = "";

    const username = document.getElementById("username_input").value;
    const api_key = document.getElementById("api_key_input").value;
    const api_secret = document.getElementById("api_secret_input").value;

    const data = {
        "api_key": api_key,
        "api_secret": api_secret,
        "username": username,
        "password": password
    };

    // Convert data to a JSON string
    const data_string = JSON.stringify(data);
    // Encrypt the data string
    const encrypted_data = encrypt.encrypt(data_string);

    $.post({
        url: "/first-time-login",
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify({ encrypted_data: encrypted_data }),
        success: function(response) {
            // Store the session id
            session_id = data.session_id
            // Hide the password prompt
            document.getElementById("password_overlay").style.display = "None";
            // Hide API data prompt
            document.getElementById("api_data").style.display = "None";
            // Get the homepage data
            get_homepage();
        },
        error: function(xhr) {
            // Display the error message
            const error_message = JSON.parse(xhr.responseText).message;
            password_message.innerHTML = error_message;
        }
    });

    // Clear sensitive input areas
    document.getElementById("api_secret_input").value = "";
    password_input.value = "";
}

// Function to verify the entered password
function verify_password() {
    // Get entered password
    const password = password_input.value;

    // Set message text to empty
    password_message.innerHTML = "";

    const data = {
        "password": password
    };

    // Convert data to a JSON string
    const data_string = JSON.stringify(data);
    // Encrypt the data string
    const encrypted_data = encrypt.encrypt(data_string);

    $.post({
        url: "/verify-password",
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify({ encrypted_data: encrypted_data }),
        success: function(data) {
            // Store the session id
            session_id = data.session_id
            // Hide the password prompt
            document.getElementById("password_overlay").style.display = "None";
            // Get the homepage data
            get_homepage();
        },
        error: function(xhr) {
            // Display the error message
            const error_message = JSON.parse(xhr.responseText).message;
            password_message.innerHTML = error_message;
        }
    });

    // Clear sensitive input areas
    password_input.value = "";
}

// Listener for the login button
document.getElementById("password_button").addEventListener("click", () => {
    if (has_api_data) {
        verify_password();
    } else {
        first_time_login();
    };
});

function post_error(xhr) {
    const error_message = JSON.parse(xhr.responseText).message;
    console.log(error_message);
    if (error_message == "Expired token") {
        // Set password screen title correctly
        document.getElementById("password_header").innerHTML = "Sorry, the session expired!"
        // Show password screen
        document.getElementById("password_overlay").style.display = "block";
    };
}

// Function to call when use token button is clicked
function use_token() {
    $.post({
        url: "/verify-token",
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify({ session_id: session_id }),
        error: post_error
    });
};

