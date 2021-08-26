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
            updateTotalAmount($(this));
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
            addNewRecord($(this));
        });
    $(".btn-del-record")
        .on("click", function () {
            deleteRecord($(this));
        });
});

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
    request.onload = function() {
        if (this.status === 200) {
            accountOptions = JSON.parse(this.responseText);
            $(".record-account").each(function () {
                initializeAccountOptions($(this));
            });
        }
    };
    request.open("GET", $("#account-option-url").val(), true);
    request.send();
}

/**
 * Initialize the account options.
 *
 * @param {jQuery} account the account select element
 * @private
 */
function initializeAccountOptions(account) {
    const type = account.data("type");
    const selectedAccount = account.val();
    let isCash = false;
    if (type === "debit") {
        isCash = ($(".credit-record").length === 0);
    } else if (type === "credit") {
        isCash = ($(".debit-record").length === 0);
    }
    account.html("");
    if (selectedAccount === "") {
        account.append($("<option/>"));
    }
    const headerInUse = $("<option/>")
        .attr("disabled", "disabled")
        .text(accountOptions["header_in_use"]);
    account.append(headerInUse);
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
        account.append(option);
    });
    const headerNotInUse = $("<option/>")
        .attr("disabled", "disabled")
        .text(accountOptions["header_not_in_use"]);
    account.append(headerNotInUse);
    accountOptions[type + "_not_in_use"].forEach(function (item) {
        const option = $("<option/>")
            .attr("value", item["code"])
            .text(item["code"] + " " + item["title"]);
        if (String(item["code"]) === selectedAccount) {
            option.attr("selected", "selected");
        }
        account.append(option);
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
 * @param {jQuery} element the amount element that changed, or the
 *                         button that was hit to delete a record
 * @private
 */
function updateTotalAmount(element) {
    const type = element.data("type")
    let total = new Decimal("0");
    $("." + type + "-to-sum").each(function () {
        if (this.value !== "") {
            total = total.plus(new Decimal(this.value));
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
 * @param {jQuery} button the button element that was hit to add a
 *                        new record
 * @private
 */
function addNewRecord(button) {
    const type = button.data("type");
    // Finds the new number that is the maximum number plus 1.
    let newNo = 0;
    $("." + type + "-record").each(function () {
        const no = parseInt($(this).data("no"));
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
    $("#" + type + "-records").append(
        JSON.parse($("#new-record-template").val())
            .replace(/TTT/g, type)
            .replace(/NNN/g, String(newNo)));
    $("#" + type + "-" + newNo + "-account")
        .on("focus", function () {
            removeBlankOption(this);
        })
        .on("blur", function () {
            validateAccount(this);
        })
        .each(function () {
            initializeAccountOptions($(this));
        });
    $("#" + type + "-" + newNo + "-summary")
        .on("blur", function () {
            validateSummary(this);
        })
        .on("click", function () {
            if (typeof startSummaryHelper === "function") {
                startSummaryHelper($(this));
            }
        });
    $("#" + type + "-" + newNo + "-amount")
        .on("blur", function () {
            validateAmount(this);
        })
        .on("change", function () {
            updateTotalAmount($(this));
            validateBalance();
        });
    $("#" + type + "-" + newNo + "-delete")
        .on("click", function () {
            deleteRecord($(this));
        });
    $("#" + type + "-" + newNo + "-m-delete")
        .on("click", function () {
            deleteRecord($(this));
        });
}

/**
 * Deletes a record.
 *
 * @param {jQuery} button the button element that was hit to delete
 *                        this record
 * @private
 */
function deleteRecord(button) {
    const type = button.data("type");
    const no = button.data("no");
    console.log("#" + type + "-" + no);
    $("#" + type + "-" + no).remove();
    resetRecordOrders(type);
    resetRecordButtons();
    updateTotalAmount(button);
    validateBalance();
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
    $(".debit-record").each(function () {
        isValidated = isValidated && validateRecord(this);
    });
    $(".credit-account").each(function () {
        isValidated = isValidated && validateRecord(this);
    });
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
        errorMessage.text(gettext("Please fill in the date."));
        return false;
    }
    date.classList.remove("is-invalid");
    errorMessage.text("");
    return true;
}

/**
 * Validates the record.
 *
 * @param {HTMLLIElement} record the record
 * @returns {boolean} true if the validation succeed, or false
 *                    otherwise
 * @private
 */
function validateRecord(record) {
    return !record.classList.contains("list-group-item-danger");
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
        errorMessage.text(gettext("Please select the account."));
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
        errorMessage.text(gettext("This summary is too long (max. 128 characters)."));
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
        errorMessage.text(gettext("Please fill in the amount."));
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
    let debitTotal = new Decimal("0");
    $(".debit-to-sum").each(function () {
        if (this.value !== "") {
            debitTotal = debitTotal.plus(new Decimal(this.value));
        }
    });
    let creditTotal = new Decimal("0");
    $(".credit-to-sum").each(function () {
        if (this.value !== "") {
            creditTotal = creditTotal.plus(new Decimal(this.value));
        }
    });
    if (!debitTotal.equals(creditTotal)) {
        balanceRows.addClass("is-invalid");
        errorMessages.text(gettext("The total amount of debit and credit records are inconsistent."))
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
        errorMessage.text(gettext("These notes are too long (max. 128 characters)."));
        return false;
    }
    note.classList.remove("is-invalid");
    errorMessage.text("");
    return true;
}
