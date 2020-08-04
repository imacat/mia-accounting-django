/* The Mia Website
 * transaction-form.js: The JavaScript for the transaction form
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
 * First written: 2019/9/19
 */

// Initializes the page JavaScript.
$(function () {
    getAccountOptions();
    resetRecordButtons();
    $("#txn-date")
        .on("blur", function () {
            validateDate();
        });
    $(".record-account")
        .on("focus", function () {
            removeBlankOption(this);
        })
        .on("blur", function () {
            validateAccount(this);
        });
    $(".record-summary")
        .on("blur", function () {
            validateSummary(this);
        });
    $(".record-amount")
        .on("blur", function () {
            validateAmount(this);
        })
        .on("change", function () {
            updateTotalAmount(this);
            validateBalance();
        });
    $("#txn-note")
        .on("blur", function () {
            validateNote();
        });
    $("#txn-form")
        .on("submit", function () {
            return validateForm();
        });
    $(".btn-new")
        .on("click", function () {
            addNewRecord(this);
        });
    $(".btn-del-record")
        .on("click", function () {
            deleteRecord(this);
        });
});

/**
 * The localized messages
 * @type {Array.}
 * @private
 */
let l10n = null;

/**
 * Returns the localization of a message.
 *
 * @param {string} key the message key
 * @returns {string} the localized message
 * @private
 */
function __(key) {
    if (l10n === null) {
        l10n = JSON.parse($("#l10n-messages").val());
    }
    if (key in l10n) {
        return l10n[key];
    }
    return key;
}

/**
 * Returns whether this is a transfer transaction.
 *
 * @returns {boolean} true if this is a transfer transaction, or false
 *                    otherwise
 * @private
 */
function isTransfer() {
    return $("#debit-records").length > 0 && $("#credit-records").length > 0;
}

/**
 * The account options
 * @type {Array.}
 * @private
 */
let accountOptions;

/**
 *  Obtains the account options.
 *
 * @private
 */
function getAccountOptions() {
    const request = new XMLHttpRequest();
    request.onreadystatechange = function() {
        if (this.readyState === 4 && this.status === 200) {
            accountOptions = JSON.parse(this.responseText);
            $(".record-account").each(function () {
                initializeAccountOptions(this);
            });
        }
    };
    request.open("GET", $("#account-option-url").val(), true);
    request.send();
}

/**
 * Initialize the account options.
 *
 * @param {HTMLSelectElement} account the account select element
 * @private
 */
function initializeAccountOptions(account) {
    const jAccount = $(account);
    const type = account.id.substring(0, account.id.indexOf("-"));
    const selectedAccount = account.value;
    let isCash = false;
    if (type === "debit") {
        isCash = ($(".credit-record").length === 0);
    } else if (type === "credit") {
        isCash = ($(".debit-record").length === 0);
    }
    jAccount.html("");
    if (selectedAccount === "") {
        jAccount.append($("<option/>"));
    }
    const headerInUse = $("<option/>")
        .attr("disabled", "disabled")
        .text(accountOptions["header_in_use"]);
    jAccount.append(headerInUse);
    accountOptions[type + "_in_use"].forEach(function (item) {
        // Skips the cash account on cash transactions.
        if (item["code"] === 1111 && isCash) {
            return;
        }
        const option = $("<option/>")
            .attr("value", item["code"])
            .text(item["code"] + " " + item["title"]);
        if (String(item["code"]) === selectedAccount) {
            option.attr("selected", "selected");
        }
        jAccount.append(option);
    });
    const headerNotInUse = $("<option/>")
        .attr("disabled", "disabled")
        .text(accountOptions["header_not_in_use"]);
    jAccount.append(headerNotInUse);
    accountOptions[type + "_not_in_use"].forEach(function (item) {
        const option = $("<option/>")
            .attr("value", item["code"])
            .text(item["code"] + " " + item["title"]);
        if (String(item["code"]) === selectedAccount) {
            option.attr("selected", "selected");
        }
        jAccount.append(option);
    });
}

/**
 * Removes the dummy blank option.
 *
 * @param {HTMLSelectElement} select the select element
 * @private
 */
function removeBlankOption(select) {
    $(select).children().each(function () {
        if (this.value === "" && !this.disabled) {
            $(this).remove();
        }
    });
}

/**
 * Updates the total amount.
 *
 * @param {HTMLButtonElement|HTMLInputElement} element the amount
 *                                                     element that
 *                                                     changed, or the
 *                                                     button that
 *                                                     was hit to
 *                                                     delete a record
 * @private
 */
function updateTotalAmount(element) {
    const type = element.id.substring(0, element.id.indexOf("-"));
    let total = 0;
    $("." + type + "-to-sum").each(function () {
        if (this.value !== "") {
            total += parseInt(this.value);
        }
    });
    total = String(total);
    while (total.match(/^[1-9][0-9]*[0-9]{3}/)) {
        total = total.replace(/^([1-9][0-9]*)([0-9]{3})/, "$1,$2");
    }
    $("#" + type + "-total").text(total);
}

/**
 * Adds a new accounting record.
 *
 * @param {HTMLButtonElement} button the button element that was hit
 *                                   to add a new record
 * @private
 */
function addNewRecord(button) {
    const type = button.id.substring(0, button.id.indexOf("-"));
    // Finds the new number that is the maximum number plus 1.
    let newNo = 0;
    $("." + type + "-record").each(function () {
        const no = parseInt(this.id.substring(type.length + 1));
        if (newNo < no) {
            newNo = no;
        }
    });
    newNo++;

    // Inserts a new table row for the new accounting record.
    insertNewRecord(type, newNo);
    // Resets the order of the records.
    resetRecordOrders(type);
    // Resets the sort and delete buttons for the records.
    resetRecordButtons();
}

/**
 * Inserts a new accounting record.
 *
 * @param {string} type the record type, either "debit" or "credit"
 * @param {number} newNo the number of this new accounting record
 * @private
 */
function insertNewRecord(type, newNo) {
    if (isTransfer()) {
        insertNewTransferRecord(type, newNo);
    } else {
        insertNewNonTransferRecord(type, newNo);
    }
}

/**
 * Inserts a new accounting record for a transfer transaction.
 *
 * @param {string} type the record type, either "debit" or "credit"
 * @param {number} newNo the number of this new accounting record
 * @private
 */
function insertNewTransferRecord(type, newNo) {
    const divAccount = createAccountBlock(type, newNo)
        .addClass("col-sm-12");
    const divAccountRow = $("<div/>")
        .addClass("row")
        .append(divAccount);

    const divSummary = createSummaryBlock(type, newNo)
        .addClass("col-lg-8");
    const divAmount = createAmountBlock(type, newNo)
        .addClass("col-lg-4");
    const divSummaryAmountRow = $("<div/>")
        .addClass("row")
        .append(divSummary, divAmount);

    const divContent = $("<div/>")
        .append(divAccountRow)
        .append(divSummaryAmountRow);

    const divBtnGroup = createActionButtonBlock(
        type, newNo, type + "-" + newNo + "-delete")
        .addClass("btn-group-vertical");
    const divActions = $("<div/>")
        .append(divBtnGroup);

    $("<li/>")
        .attr("id", type + "-" + newNo)
        .addClass("list-group-item")
        .addClass("d-flex")
        .addClass(type + "-record")
        .append(divContent, divActions)
        .appendTo("#" + type + "-records");
}

/**
 * Inserts a new accounting record for a non-transfer transaction.
 *
 * @param {string} type the record type, either "debit" or "credit"
 * @param {number} newNo the number of this new accounting record
 * @private
 */
function insertNewNonTransferRecord(type, newNo) {
    const divAccount = createAccountBlock(type, newNo)
        .addClass("col-lg-6");

    const divSummary = createSummaryBlock(type, newNo)
        .addClass("col-sm-8");
    const divAmount = createAmountBlock(type, newNo)
        .addClass("col-sm-4");
    const divSummaryAmountRow = $("<div/>")
        .addClass("row")
        .append(divSummary, divAmount);
    const divSummaryAmount = $("<div/>")
        .addClass("col-lg-6")
        .append(divSummaryAmountRow);

    const divContent = $("<div/>")
        .addClass("row")
        .append(divAccount, divSummaryAmount);

    const divBtnGroup = createActionButtonBlock(
        type, newNo, type + "-" + newNo + "-delete")
        .addClass("btn-group")
        .addClass("d-none d-lg-flex");
    const divBtnGroupVertical = createActionButtonBlock(
        type, newNo, type + "-" + newNo + "-m-delete")
        .addClass("btn-group-vertical")
        .addClass("d-lg-none");
    const divActions = $("<div/>")
        .append(divBtnGroup, divBtnGroupVertical);

    $("<li/>")
        .attr("id", type + "-" + newNo)
        .addClass("list-group-item")
        .addClass("d-flex")
        .addClass("justify-content-between")
        .addClass(type + "-record")
        .append(divContent, divActions)
        .appendTo("#" + type + "-records");
}

/**
 * Creates and returns a new <div></div> account block.
 *
 * @param {string} type the record type, either "debit" or "credit"
 * @param {number} newNo the number of this new accounting record
 * @returns {JQuery<HTMLElement>} the new <div></div> account block
 * @private
 */
function createAccountBlock(type, newNo) {
    const order = $("<input/>")
        .attr("id", type + "-" + newNo + "-ord")
        .attr("type", "hidden")
        .attr("name", type + "-" + newNo + "-ord")
        .addClass(type + "-ord");
    const account = $("<select/>")
        .attr("id", type + "-" + newNo + "-account")
        .attr("name", type + "-" + newNo + "-account")
        .addClass("form-control")
        .addClass("record-account")
        .addClass(type + "-account")
        .on("focus", function () {
            removeBlankOption(this);
        })
        .on("blur", function () {
            validateAccount(this);
        })
        .each(function () {
            initializeAccountOptions(this);
        });
    const accountError = $("<div/>")
        .attr("id", type + "-" + newNo + "-account-error")
        .addClass("invalid-feedback");
    return $("<div/>")
        .append(order, account, accountError);
}

/**
 * Creates and returns a new <div></div> summary block.
 *
 * @param {string} type the record type, either "debit" or "credit"
 * @param {number} newNo the number of this new accounting record
 * @returns {JQuery<HTMLElement>} the new <div></div> summary block
 * @private
 */
function createSummaryBlock(type, newNo) {
    const summary = $("<input/>")
        .attr("id", type + "-" + newNo + "-summary")
        .attr("type", "text")
        .attr("name", type + "-" + newNo + "-summary")
        .addClass("form-control")
        .addClass("record-summary")
        .on("blur", function () {
            validateSummary(this);
        });
    if (typeof startSummaryHelper === "function") {
        summary
            .attr("data-toggle", "modal")
            .attr("data-target", "#summary-modal")
            .on("click", function () {
                startSummaryHelper(this);
            });
    }
    const summaryError = $("<div/>")
        .attr("id", type + "-" + newNo + "-summary-error")
        .addClass("invalid-feedback");
    return $("<div/>")
        .append(summary, summaryError);
}

/**
 * Creates and returns a new <div></div> amount block.
 *
 * @param {string} type the record type, either "debit" or "credit"
 * @param {number} newNo the number of this new accounting record
 * @returns {JQuery<HTMLElement>} the new <div></div> amount block
 * @private
 */
function createAmountBlock(type, newNo) {
    const amount = $("<input/>")
        .attr("id", type + "-" + newNo + "-amount")
        .attr("type", "number")
        .attr("name", type + "-" + newNo + "-amount")
        .attr("min", 1)
        .attr("required", "required")
        .addClass("form-control")
        .addClass("record-amount")
        .addClass(type + "-to-sum")
        .on("blur", function () {
            validateAmount(this);
        })
        .on("change", function () {
            updateTotalAmount(this);
            validateBalance();
        });
    const amountError = $("<div/>")
        .attr("id", type + "-" + newNo + "-amount-error")
        .addClass("invalid-feedback");
    return $("<div/>")
        .append(amount, amountError);
}

/**
 * Creates and returns a new <div></div> action button block.
 *
 * @param {string} type the record type, either "debit" or "credit"
 * @param {number} newNo the number of this new accounting record
 * @param {string} btnDelId the ID of the delete button
 * @returns {JQuery<HTMLElement>} the new <div></div> button block
 * @private
 */
function createActionButtonBlock(type, newNo, btnDelId) {
    const btnSort = $("<button/>")
        .attr("type", "button")
        .addClass("btn btn-outline-secondary")
        .addClass("btn-sort-" + type)
        .append($("<i/>").addClass("fas fa-sort"));
    const btnDelete = $("<button/>")
        .attr("id", btnDelId)
        .attr("type", "button")
        .addClass("btn btn-danger")
        .addClass("btn-del-record")
        .addClass("btn-del-" + type)
        .on("click", function () {
            deleteRecord(this);
        })
        .append($("<i/>").addClass("fas fa-trash"));
    return $("<div/>")
        .addClass("btn-actions-" + type)
        .append(btnSort, btnDelete);
}

/**
 * Deletes a record.
 *
 * @param {HTMLButtonElement} button the button element that was hit
 *                            to delete this record
 * @private
 */
function deleteRecord(button) {
    const type = button.id.substring(0, button.id.indexOf("-"));
    const no = parseInt(button.id.substring(type.length + 1, button.id.indexOf("-", type.length + 1)));
    $("#" + type + "-" + no).remove();
    resetRecordOrders(type);
    resetRecordButtons();
    updateTotalAmount(button);
}

/**
 * Resets the order of the records according to their appearance.
 *
 * @param {string} type the record type, either "debit" or "credit".
 * @private
 */
function resetRecordOrders(type) {
    const sorted = $("#" + type + "-records").sortable("toArray");
    for (let i = 0; i < sorted.length; i++) {
        $("#" + sorted[i] + "-ord")[0].value = i + 1;
    }
}

/**
 * Resets the sort and delete buttons for the records.
 *
 * @private
 */
function resetRecordButtons() {
    ["debit", "credit"].forEach(function (type) {
        const records = $("." + type + "-record");
        if (records.length > 1) {
            $("#" + type + "-records").sortable({
                classes: {
                    "ui-sortable-helper": "list-group-item-secondary",
                },
                cursor: "move",
                cancel: "input, select",
                stop: function () {
                    resetRecordOrders(type);
                },
            }).sortable("enable");
            $(".btn-actions-" + type).removeClass("invisible");
        } else if (records.length === 1) {
            $("#" + type + "-records").sortable().sortable("disable");
            $(".btn-actions-" + type).addClass("invisible");
        }
    });
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
    isValidated = isValidated && validateDate();
    $(".record-account").each(function () {
        isValidated = isValidated && validateAccount(this);
    });
    $(".record-summary").each(function () {
        isValidated = isValidated && validateSummary(this);
    });
    $(".record-amount").each(function () {
        isValidated = isValidated && validateAmount(this);
    });
    if (isTransfer()) {
        isValidated = isValidated && validateBalance();
    }
    isValidated = isValidated && validateNote();
    return isValidated;
}

/**
 * Validates the date column.
 *
 * @returns {boolean} true if the validation succeed, or false
 *                    otherwise
 * @private
 */
function validateDate() {
    const date = $("#txn-date")[0];
    const errorMessage = $("#txn-date-error");
    if (date.value === "") {
        date.classList.add("is-invalid");
        errorMessage.text(__("Please fill in the date."));
        return false;
    }
    date.classList.remove("is-invalid");
    errorMessage.text("");
    return true;
}

/**
 * Validates the account column.
 *
 * @param {HTMLSelectElement} account the account selection element
 * @returns {boolean} true if the validation succeed, or false
 *                    otherwise
 * @private
 */
function validateAccount(account) {
    const errorMessage = $("#" + account.id + "-error");
    if (account.value === "") {
        account.classList.add("is-invalid");
        errorMessage.text(__("Please select the account."));
        return false;
    }
    account.classList.remove("is-invalid");
    errorMessage.text("");
    return true;
}

/**
 * Validates the summary column.
 *
 * @param {HTMLInputElement} summary the summary input element
 * @returns {boolean} true if the validation succeed, or false
 *                    otherwise
 * @private
 */
function validateSummary(summary) {
    const errorMessage = $("#" + summary.id + "-error");
    summary.value = summary.value.trim();
    if (summary.value.length > 128) {
        summary.classList.add("is-invalid");
        errorMessage.text(__("This summary is too long (max. 128 characters)."));
        return false;
    }
    summary.classList.remove("is-invalid");
    errorMessage.text("");
    return true;
}

/**
 * Validates the amount column.
 *
 * @param {HTMLInputElement} amount the amount input element
 * @returns {boolean} true if the validation succeed, or false
 *                    otherwise
 * @private
 */
function validateAmount(amount) {
    const errorMessage = $("#" + amount.id + "-error");
    amount.value = amount.value.trim();
    if (amount.value === "") {
        amount.classList.add("is-invalid");
        errorMessage.text(__("Please fill in the amount."));
        return false;
    }
    amount.classList.remove("is-invalid");
    errorMessage.text("");
    return true;
}

/**
 * Validates the balance between debit and credit records
 *
 * @returns {boolean} true if the validation succeed, or false
 *                    otherwise
 * @private
 */
function validateBalance() {
    const balanceRows = $(".balance-row");
    const errorMessages = $(".balance-error");
    let debitTotal = 0;
    $(".debit-to-sum").each(function () {
        if (this.value !== "") {
            debitTotal += parseInt(this.value);
        }
    });
    let creditTotal = 0;
    $(".credit-to-sum").each(function () {
        if (this.value !== "") {
            creditTotal += parseInt(this.value);
        }
    });
    if (debitTotal !== creditTotal) {
        balanceRows.addClass("is-invalid");
        errorMessages.text(__("The sum of debit and credit are inconsistent."))
        return false;
    }
    balanceRows.removeClass("is-invalid");
    errorMessages.text("");
    return true;
}

/**
 * Validates the note column.
 *
 * @returns {boolean} true if the validation succeed, or false
 *                    otherwise
 * @private
 */
function validateNote() {
    const note = $("#txn-note")[0];
    const errorMessage = $("#txn-note-error");
    note.value = note.value.trim();
    if (note.value.length > 128) {
        note.classList.add("is-invalid");
        errorMessage.text(__("This note is too long (max. 128 characters)."));
        return false;
    }
    note.classList.remove("is-invalid");
    errorMessage.text("");
    return true;
}
