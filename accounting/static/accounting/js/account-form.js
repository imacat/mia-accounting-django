/* The Mia Website
 * account-form.js: The JavaScript to edit an account
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
 * First written: 2020/3/23
 */

// Initializes the page JavaScript.
$(function () {
    getAllAccounts();
    $("#account-code").on("blur", function () {
        updateParent(this);
        validateCode();
    });
    $("#account-title").on("blur", function () {
        validateTitle();
    });
    $("#account-form").on("submit", function () {
        return validateForm();
    });
});

/**
 * All the accounts
 * @type {Array.}
 * @private
 */
let accounts;

/**
 * Obtains all the accounts.
 *
 * @private
 */
function getAllAccounts() {
    const request = new XMLHttpRequest();
    request.onreadystatechange = function() {
        if (this.readyState === 4 && this.status === 200) {
            accounts = JSON.parse(this.responseText);
        }
    };
    request.open("GET", $("#all-account-url").val(), true);
    request.send();
}

/**
 * Updates the parent account.
 *
 * @param {HTMLInputElement} code the code input element
 * @private
 */
function updateParent(code) {
    const parent = $("#account-parent");
    if (code.value.length === 0) {
        parent.text("");
        return;
    }
    if (code.value.length === 1) {
        parent.text(gettext("Topmost"));
        return;
    }
    const parentCode = code.value.substr(0, code.value.length - 1);
    if (parentCode in accounts) {
        parent.text(parentCode + " " + accounts[parentCode]);
        return;
    }
    parent.text(gettext("(Unknown)"));
}


/*******************
 * Form Validation *
 *******************/

/**
 * Validates the form.
 *
 * @returns {boolean} true if the validation succeed, or false
 *                    otherwise
 * @private
 */
function validateForm() {
    let isValidated = true;
    isValidated = isValidated && validateCode();
    isValidated = isValidated && validateTitle();
    return isValidated;
}

/**
 * Validates the code column.
 *
 * @returns {boolean} true if the validation succeed, or false
 *                    otherwise
 * @private
 */
function validateCode() {
    const code = $("#account-code")[0];
    const errorMessage = $("#account-code-error");
    code.value = code.value.trim();
    if (code.value === "") {
        code.classList.add("is-invalid");
        errorMessage.text(gettext("Please fill in the code."));
        return false;
    }
    if (!code.value.match(/^[1-9][0-9]*$/)) {
        code.classList.add("is-invalid");
        errorMessage.text(gettext("You can only use a number as the code"));
        return false;
    }
    const originalCode = $("#account-code-original").val();
    if (code.value !== originalCode) {
        if (originalCode !== "" && code.value.startsWith(originalCode)) {
            code.classList.add("is-invalid");
            errorMessage.text(gettext("You cannot set the code under itself."));
            return false;
        }
        if (code.value in accounts) {
            code.classList.add("is-invalid");
            errorMessage.text(gettext("This code is already in use."));
            return false;
        }
    }
    const parentCode = code.value.substr(0, code.value.length - 1);
    if (!(parentCode in accounts)) {
        code.classList.add("is-invalid");
        errorMessage.text(gettext("The parent account of this code does not exist."));
        return false;
    }
    if (originalCode !== "" && code.value !== originalCode) {
        const descendants = [];
        Object.keys(accounts).forEach(function (key) {
            if (key.startsWith(originalCode) && key !== originalCode) {
                descendants.push(key);
            }
        });
        if (descendants.length > 0) {
            descendants.sort(function (a, b) {
                return b.length - a.length;
            });
            if (descendants[0].length
                - originalCode.length
                + code.value.length > code.maxLength) {
                code.classList.add("is-invalid");
                errorMessage.text(gettext("The descendant account codes will be too long  (max. 5)."));
                return false;
            }
        }
    }
    code.classList.remove("is-invalid");
    errorMessage.text("");
    return true;
}

/**
 * Validates the title column.
 *
 * @returns {boolean} true if the validation succeed, or false
 *                    otherwise
 * @private
 */
function validateTitle() {
    const title = $("#account-title")[0];
    const errorMessage = $("#account-title-error");
    title.value = title.value.trim();
    if (title.value === "") {
        title.classList.add("is-invalid");
        errorMessage.text(gettext("Please fill in the title."));
        return false;
    }
    title.classList.remove("is-invalid");
    errorMessage.text("");
    return true;
}
