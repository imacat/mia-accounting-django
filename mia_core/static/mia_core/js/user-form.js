/* The Mia Website
 * edit.js: The JavaScript to edit the user data
 */

/*  Copyright (c) 2019-2020 imacat.
 *
 *  Licensed under the Apache License, Version 2.0 (the "License");
 *  you may not use this file except in compliance with the License.
 *  You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
 */

/* Author: imacat@mail.imacat.idv.tw (imacat)
 * First written: 2020/3/26
 */

// Initializes the page JavaScript.
$(function () {
    $("#user-login-id").on("blur", function () {
        validateLoginId();
    });
    $("#user-password").on("blur", function () {
        validatePassword();
    });
    $("#user-password2").on("blur", function () {
        validatePassword2();
    });
    $("#user-name").on("blur", function () {
        validateName();
    });
    $("#user-form").on("submit", function () {
        return validateForm();
    });
});


/*******************
 * Form Validation *
 *******************/

/**
 * The validation result
 * @type {object}
 * @private
 */
let isValidated;

/**
 * Validates the form.
 *
 * @returns {boolean} true if the validation succeed, or false
 *                    otherwise
 * @private
 */
function validateForm() {
    isValidated = {
        "id": null,
        "_sync": true,
    };
    validateLoginIdAsync().then();
    validateSyncColumns();
    return false;
}

/**
 * Validates the form on synchronous validations.
 *
 * @private
 */
function validateSyncColumns() {
    let isSyncValidated = true;
    isSyncValidated = isSyncValidated && validatePassword();
    isSyncValidated = isSyncValidated && validatePassword2();
    isSyncValidated = isSyncValidated && validateName();
    isValidated["_sync"] = isSyncValidated;
    validateFormAsync();
}

/**
 * Validates the form for the asynchronous validation.
 *
 * @private
 */
function validateFormAsync() {
    let isFormValidated = true;
    const keys = Object.keys(isValidated);
    for (let i = 0; i < keys.length; i++) {
        if (isValidated[keys[i]] === null) {
            return;
        }
        isFormValidated = isFormValidated && isValidated[keys[i]];
    }
    if (isFormValidated) {
        $("#user-form")[0].submit();
    }
}

/**
 * Validates the log in ID for asynchronous form validation.
 *
 * @returns {Promise<void>}
 * @private
 */
async function validateLoginIdAsync() {
    isValidated["id"] = await validateLoginId();
    validateFormAsync();
}

/**
 * Validates the log in ID.
 *
 * @returns {boolean} true if the validation succeed, or false
 *                    otherwise
 * @private
 */
async function validateLoginId() {
    const id = $("#user-login-id")[0];
    const errorMessage = $("#user-login-id-error");
    id.value = id.value.trim();
    if (id.value === "") {
        id.classList.add("is-invalid");
        errorMessage.text(gettext("Please fill in the log in ID."));
        return false;
    }
    if (id.value.match(/\//)) {
        id.classList.add("is-invalid");
        errorMessage.text(gettext("You cannot use slash (/) in the log in ID."));
        return false;
    }
    const originalId = $("#user-login-id-original").val();
    if (originalId === "" || id.value !== originalId) {
        let exists = null;
        const request = new XMLHttpRequest();
        request.onreadystatechange = function() {
            if (this.readyState === 4 && this.status === 200) {
                exists = JSON.parse(this.responseText);
            }
        };
        const url = $("#exists-url").val().replace("ID", id.value);
        request.open("GET", url, true);
        request.send();
        while (exists === null) {
            await new Promise(r => setTimeout(r, 200));
        }
        if (exists) {
            id.classList.add("is-invalid");
            errorMessage.text(gettext("This log in ID is already in use."));
            return false;
        }
    }
    id.classList.remove("is-invalid");
    errorMessage.text("");
    return true;
}

/**
 * Validates the password.
 *
 * @returns {boolean} true if the validation succeed, or false
 *                    otherwise
 * @private
 */
async function validatePassword() {
    const password = $("#user-password")[0];
    const errorMessage = $("#user-password-error");
    password.value = password.value.trim();
    if (password.required) {
        if (password.value === "") {
            password.classList.add("is-invalid");
            errorMessage.text(gettext("Please fill in the password."));
            return false;
        }
    }
    password.classList.remove("is-invalid");
    errorMessage.text("");
    return true;
}

/**
 * Validates the password verification.
 *
 * @returns {boolean} true if the validation succeed, or false
 *                    otherwise
 * @private
 */
function validatePassword2() {
    const password2 = $("#user-password2")[0];
    const errorMessage = $("#user-password2-error");
    password2.value = password2.value.trim();
    const password = $("#user-password").val();
    if (password !== "") {
        if (password2.value === "") {
            password2.classList.add("is-invalid");
            errorMessage.text(gettext("Please enter the password again to verify it."));
            return false;
        }
    }
    if (password2.value !== password) {
        password2.classList.add("is-invalid");
        errorMessage.text(gettext("The two passwords do not match."));
        return false;
    }
    password2.classList.remove("is-invalid");
    errorMessage.text("");
    return true;
}

/**
 * Validates the name.
 *
 * @returns {boolean} true if the validation succeed, or false
 *                    otherwise
 * @private
 */
function validateName() {
    const name = $("#user-name")[0];
    const errorMessage = $("#user-name-error");
    name.value = name.value.trim();
    if (name.value === "") {
        name.classList.add("is-invalid");
        errorMessage.text(gettext("Please fill in the name."));
        return false;
    }
    name.classList.remove("is-invalid");
    errorMessage.text("");
    return true;
}
