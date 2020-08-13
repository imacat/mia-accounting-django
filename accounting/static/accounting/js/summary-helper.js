/* The Mia Website
 * summary-helper.js: The JavaScript for the summary helper
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
 * First written: 2020/4/3
 */

// Initializes the summary helper JavaScript.
$(function () {
    loadSummaryCategoryData();
    $("#summary-helper-form")
        .on("submit", function () {
            return false;
        });
    $(".record-summary")
        .on("click", function () {
            startSummaryHelper($(this));
        });
    $("#summary-summary")
        .on("change", function () {
            this.value = this.value.trim();
            // Replaced common substitution character "*" with "×"
            this.value = this.value.replace(/\*(\d+)$/, "×$1");
            parseSummaryForHelper(this.value);
        });
    $(".summary-tab")
        .on("click", function () {
            switchSummaryTab($(this));
        });
    // The general categories
    $("#summary-general-category")
        .on("change", function () {
            setSummaryGeneralCategoryButtons(this.value);
            setGeneralCategorySummary();
            setSummaryAccount("general", this.value);
        });
    // The travel routes
    $("#summary-travel-category")
        .on("change", function () {
            setSummaryTravelCategoryButtons(this.value);
            setSummaryAccount("travel", this.value);
        });
    $(".summary-travel-part")
        .on("change", function () {
            this.value = this.value.trim();
            setTravelSummary();
        });
    $(".btn-summary-travel-direction")
        .on("click", function () {
            $("#summary-travel-direction").get(0).value = this.innerText;
            setSummaryTravelDirectionButtons(this.innerText);
            setTravelSummary();
        });
    // The bus routes
    $("#summary-bus-category")
        .on("change", function () {
            setSummaryBusCategoryButtons(this.value);
            setSummaryAccount("bus", this.value);
        });
    $(".summary-bus-part")
        .on("change", function () {
            this.value = this.value.trim();
            setBusSummary();
        });
    $("#summary-count")
        .on("change", function () {
            updateSummaryCount();
        });
    $("#summary-confirm")
        .on("click", function () {
            applySummaryToAccountingRecord();
        });
});

/**
 * The known categories
 * @type {object}
 * @private
 */
let summaryCategories = null;

/**
 * The known categories and their corresponding accounts
 * @type {object}
 * @private
 */
let summaryAccounts = null;

/**
 * The account that corresponds to this category
 * @type {null|string}
 * @private
 */
let summaryAccount = null;

/**
 * Loads the summary category data.
 *
 * @private
 */
function loadSummaryCategoryData() {
    const data = JSON.parse($("#summary-categories").val());
    summaryCategories = {};
    summaryAccounts = {};
    ["debit", "credit"].forEach(function (type) {
        summaryCategories[type] = {};
        summaryAccounts[type] = {};
        ["general", "travel", "bus"].forEach(function (format) {
            summaryCategories[type][format] = [];
            summaryAccounts[type][format] = {};
            if (type + "-" + format in data) {
                data[type + "-" + format]
                    .forEach(function (item) {
                        summaryCategories[type][format].push(item[0]);
                        summaryAccounts[type][format][item[0]] = item[1];
                    });
            }
        });
    });
}

/**
 * Starts the summary helper.
 *
 * @param {jQuery} summary the summary input element
 */
function startSummaryHelper(summary) {
    // Replaced common substitution character "*" with "×"
    let summary_content = summary.val();
    summary_content = summary_content.replace(/\*(\d+)$/, "×$1");
    const type = summary.data("type");
    const no = summary.data("no");
    $("#summary-record").val(type + "-" + no);
    $("#summary-summary").val(summary_content);
    // Loads the know summary categories into the summary helper
    loadKnownSummaryCategories(type);
    // Parses the summary and sets up the summary helper
    parseSummaryForHelper(summary_content);
    // Focus on the summary input
    setTimeout(function () {
        $("#summary-summary").get(0).focus();
    }, 100);
}

/**
 * Loads the known summary categories into the summary helper.
 *
 * @param {string} type the record type, either "debit" or "credit"
 * @private
 */
function loadKnownSummaryCategories(type) {
    ["general", "travel", "bus"].forEach(function (format) {
        const knownCategories = $("#summary-" + format + "-categories-known");
        knownCategories.html("");
        summaryCategories[type][format].forEach(function (item) {
            knownCategories.append(
                $("<span/>")
                    .addClass("btn btn-outline-primary")
                    .addClass("btn-summary-helper")
                    .addClass("btn-summary-" + format + "-category")
                    .text(item));
        });
    });

    // The regular payments
    const regularPayments = getRegularPayments();
    ["debit", "credit"].forEach(function (type) {
        summaryCategories[type].regular = [];
        summaryAccounts[type].regular = {};
        regularPayments[type].forEach(function (item) {
            summaryCategories[type].regular.push(item);
            summaryAccounts[type].regular[item.title] = item.account;
        });
    });
    const regularPaymentButtons = $("#summary-regular-payments");
    regularPaymentButtons.html("");
    summaryCategories[type].regular.forEach(function (item) {
        regularPaymentButtons.append(
            $("<span/>")
                .attr("title", item.summary)
                .addClass("btn btn-outline-primary")
                .addClass("btn-summary-helper")
                .addClass("btn-summary-regular")
                .text(item.title));
    });

    $(".btn-summary-general-category")
        .on("click", function () {
            $("#summary-general-category").get(0).value = this.innerText;
            setSummaryGeneralCategoryButtons(this.innerText);
            setGeneralCategorySummary();
            setSummaryAccount("general", this.innerText);
        });
    $(".btn-summary-travel-category")
        .on("click", function () {
            $("#summary-travel-category").get(0).value = this.innerText;
            setSummaryTravelCategoryButtons(this.innerText);
            setTravelSummary();
            setSummaryAccount("travel", this.innerText);
        });
    $(".btn-summary-bus-category")
        .on("click", function () {
            $("#summary-bus-category").get(0).value = this.innerText;
            setSummaryBusCategoryButtons(this.innerText);
            setBusSummary();
            setSummaryAccount("bus", this.innerText);
        });
    $(".btn-summary-regular")
        .on("click", function () {
            $("#summary-summary").get(0).value = this.title;
            setSummaryRegularPaymentButtons(this.innerText);
            setSummaryAccount("regular", this.innerText);
        });
}

/**
 * Parses the summary and sets up the summary helper.
 *
 * @param {string} summary the summary
 */
function parseSummaryForHelper(summary) {
    // Parses the summary and sets up the category helpers.
    parseSummaryForCategoryHelpers(summary);
    // The number of items
    const pos = summary.lastIndexOf("×");
    let count = 1;
    if (pos !== -1) {
        count = parseInt(summary.substr(pos + 1));
    }
    if (count === 0) {
        count = 1;
    }
    $("#summary-count").get(0).value = count;
}

/**
 * Parses the summary and sets up the category helpers.
 *
 * @param {string} summary the summary
 */
function parseSummaryForCategoryHelpers(summary) {
    $(".btn-summary-helper")
        .removeClass("btn-primary")
        .addClass("btn-outline-primary");
    $("#btn-summary-one-way")
        .removeClass("btn-outline-primary")
        .addClass("btn-primary");
    $(".summary-helper-input").each(function () {
        this.classList.remove("is-invalid");
        if (this.id === "summary-travel-direction") {
            this.value = $("#btn-summary-one-way").text();
        } else {
            this.value = "";
        }
    });

    // A bus route
    const matchBus = summary.match(/^(.+)—(.+)—(.+)→(.+?)(?:×[0-9]+)?$/);
    if (matchBus !== null) {
        $("#summary-bus-category").get(0).value = matchBus[1];
        setSummaryBusCategoryButtons(matchBus[1]);
        setSummaryAccount("bus", matchBus[1]);
        $("#summary-bus-route").get(0).value = matchBus[2];
        $("#summary-bus-from").get(0).value = matchBus[3];
        $("#summary-bus-to").get(0).value = matchBus[4];
        switchSummaryTab($("#summary-tab-bus"));
        return;
    }

    // A general travel route
    const matchTravel = summary.match(/^(.+)—(.+)([→|↔])(.+?)(?:×[0-9]+)?$/);
    if (matchTravel !== null) {
        $("#summary-travel-category").get(0).value = matchTravel[1];
        setSummaryTravelCategoryButtons(matchTravel[1]);
        setSummaryAccount("travel", matchTravel[1]);
        $("#summary-travel-from").get(0).value = matchTravel[2];
        $("#summary-travel-direction").get(0).value = matchTravel[3];
        setSummaryTravelDirectionButtons(matchTravel[3]);
        $("#summary-travel-to").get(0).value = matchTravel[4];
        switchSummaryTab($("#summary-tab-travel"));
        return;
    }

    // A general category
    const generalCategoryTab = $("#summary-tab-category");
    const matchCategory = summary.match(/^(.+)—.+(?:×[0-9]+)?$/);
    if (matchCategory !== null) {
        $("#summary-general-category").get(0).value = matchCategory[1];
        setSummaryGeneralCategoryButtons(matchCategory[1]);
        setSummaryAccount("general", matchCategory[1]);
        switchSummaryTab(generalCategoryTab);
        return;
    }

    // A general summary text
    setSummaryGeneralCategoryButtons(null);
    setSummaryAccount("general", null);
    switchSummaryTab(generalCategoryTab);
}

/**
 * Switch the summary helper to tab.
 *
 * @param {jQuery} tab the navigation tab corresponding to a type
 *                     of helper
 * @private
 */
function switchSummaryTab(tab) {
    $(".summary-tab-content").addClass("d-none");
    $("#summary-tab-content-" + tab.data("tab")).removeClass("d-none");
    $(".summary-tab").removeClass("active");
    tab.addClass("active");
}

/**
 * Sets the known general category buttons.
 *
 * @param {string|null} category the general category
 */
function setSummaryGeneralCategoryButtons(category) {
    $(".btn-summary-general-category").each(function () {
        if (this.innerText === category) {
            this.classList.remove("btn-outline-primary");
            this.classList.add("btn-primary");
        } else {
            this.classList.add("btn-outline-primary");
            this.classList.remove("btn-primary");
        }
    });
}

/**
 * Sets the summary of a general category.
 *
 */
function setGeneralCategorySummary() {
    const summary = $("#summary-summary").get(0);
    const dashPos = summary.value.indexOf("—");
    if (dashPos !== -1) {
        summary.value = summary.value.substring(dashPos + 1);
    }
    const category = $("#summary-general-category").get(0).value;
    if (category !== "") {
        summary.value = category + "—" + summary.value;
    }
}

/**
 * Sets the known travel category buttons.
 *
 * @param {string} category the travel category
 */
function setSummaryTravelCategoryButtons(category) {
    $(".btn-summary-travel-category").each(function () {
        if (this.innerText === category) {
            this.classList.remove("btn-outline-primary");
            this.classList.add("btn-primary");
        } else {
            this.classList.add("btn-outline-primary");
            this.classList.remove("btn-primary");
        }
    });
}

/**
 * Sets the summary of a general travel.
 *
 */
function setTravelSummary() {
    $(".summary-travel-part").each(function () {
        if (this.value === "") {
            this.classList.add("is-invalid");
        } else {
            this.classList.remove("is-invalid");
        }
    });
    let summary = $("#summary-travel-category").get(0).value
        + "—" + $("#summary-travel-from").get(0).value
        + $("#summary-travel-direction").get(0).value
        + $("#summary-travel-to").get(0).value;
    const count = parseInt($("#summary-count").get(0).value);
    if (count !== 1) {
        summary = summary + "×" + count;
    }
    $("#summary-summary").get(0).value = summary;
}

/**
 * Sets the known summary travel direction buttons.
 *
 * @param {string} direction the known summary travel direction
 */
function setSummaryTravelDirectionButtons(direction) {
    $(".btn-summary-travel-direction").each(function () {
        if (this.innerText === direction) {
            this.classList.remove("btn-outline-primary");
            this.classList.add("btn-primary");
        } else {
            this.classList.add("btn-outline-primary");
            this.classList.remove("btn-primary");
        }
    });
}

/**
 * Sets the known bus category buttons.
 *
 * @param {string} category the bus category
 */
function setSummaryBusCategoryButtons(category) {
    $(".btn-summary-bus-category").each(function () {
        if (this.innerText === category) {
            this.classList.remove("btn-outline-primary");
            this.classList.add("btn-primary");
        } else {
            this.classList.add("btn-outline-primary");
            this.classList.remove("btn-primary");
        }
    });
}

/**
 * Sets the summary of a bus travel.
 *
 */
function setBusSummary() {
    $(".summary-bus-part").each(function () {
        if (this.value === "") {
            this.classList.add("is-invalid");
        } else {
            this.classList.remove("is-invalid");
        }
    });
    let summary = $("#summary-bus-category").get(0).value
        + "—" + $("#summary-bus-route").get(0).value
        + "—" + $("#summary-bus-from").get(0).value
        + "→" + $("#summary-bus-to").get(0).value;
    const count = parseInt($("#summary-count").get(0).value);
    if (count !== 1) {
        summary = summary + "×" + count;
    }
    $("#summary-summary").get(0).value = summary;
}

/**
 * Sets the regular payment buttons.
 *
 * @param {string} category the regular payment
 */
function setSummaryRegularPaymentButtons(category) {
    $(".btn-summary-regular").each(function () {
        if (this.innerText === category) {
            this.classList.remove("btn-outline-primary");
            this.classList.add("btn-primary");
        } else {
            this.classList.add("btn-outline-primary");
            this.classList.remove("btn-primary");
        }
    });
}

/**
 * Sets the account for this summary category.
 *
 * @param {string} format the category format, either "general",
 *                        "travel", or "bus".
 * @param {string|null} category the category
 */
function setSummaryAccount(format, category) {
    const recordId = $("#summary-record").get(0).value;
    const type = recordId.substring(0, recordId.indexOf("-"));
    if (category in summaryAccounts[type][format]) {
        summaryAccount = summaryAccounts[type][format][category];
    } else {
        summaryAccount = null;
    }
}

/**
 * Updates the count.
 *
 * @private
 */
function updateSummaryCount() {
    const count = parseInt($("#summary-count").val());
    const summary = $("#summary-summary").get(0);
    const pos = summary.value.lastIndexOf("×");
    if (pos === -1) {
        if (count !== 1) {
            summary.value = summary.value + "×" + count;
        }
    } else {
        const content = summary.value.substring(0, pos);
        if (count === 1) {
            summary.value = content;
        } else {
            summary.value = content + "×" + count;
        }
    }
}

/**
 * Applies the summary to the accounting record.
 *
 * @private
 */
function applySummaryToAccountingRecord() {
    const recordId = $("#summary-record").get(0).value;
    const summary = $("#" + recordId + "-summary").get(0);
    summary.value = $("#summary-summary").get(0).value.trim();
    const account = $("#" + recordId + "-account").get(0);
    if (summaryAccount !== null && account.value === "") {
        account.value = summaryAccount;
    }
    setTimeout(function () {
        summary.blur();
    }, 100);
}
