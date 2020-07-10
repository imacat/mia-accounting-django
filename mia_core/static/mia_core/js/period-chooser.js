/* The Mia Website
 * period-chooser.js: The JavaScript for the period chooser
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
 * First written: 2019/9/14
 */

// Initializes the period chooser JavaScript.
$(function () {
    $(".period-tab")
        .on("click", function () {
            switchPeriodTab(this);
        });
    $("#button-period-day")
        .on("click", function () {
            window.location = $("#period-url").val()
                .replace("period-spec", $("#day-picker").val());
        });
    $("#period-start")
        .on("change", function () {
            $("#period-end")[0].min = this.value;
        });
    $("#period-end")
        .on("change", function () {
            $("#period-start")[0].max = this.value;
        });
    $("#button-period-custom")
        .on("click", function () {
            window.location = $("#period-url").val().replace(
                "period-spec",
                $("#period-start").val() + "-" + $("#period-end").val());
        });

    const monthPickerParams = JSON.parse($("#period-month-picker-params").val());
    const monthPicker = $("#month-picker");
    monthPicker.datetimepicker({
        locale: monthPickerParams.locale,
        inline: true,
        format: "YYYY-MM",
        minDate: monthPickerParams.minDate,
        maxDate: monthPickerParams.maxDate,
        useCurrent: false,
        defaultDate: monthPickerParams.defaultDate,
    });
    monthPicker.on("change.datetimepicker", function (e) {
        monthPickerChanged(e.date);
    });
});

/**
 * Turns to the page to view the records of a month when the month is
 * selected.
 *
 * @param {moment} newDate the date with the selected new month
 * @private
 */
function monthPickerChanged(newDate) {
    const year = newDate.year();
    const month = newDate.month() + 1;
    let periodSpec;
    if (month < 10) {
        periodSpec = year + "-0" + month;
    } else {
        periodSpec = year + "-" + month;
    }
    window.location = $("#period-url").val()
        .replace("period-spec", periodSpec);
}

/**
 * Switch the period chooser to tab.
 *
 * @param {HTMLElement} tab the navigation tab corresponding to a type
 *                          of period
 * @private
 */
function switchPeriodTab(tab) {
    const tabName = tab.id.substr("period-tab-".length);
    $(".period-content").each(function () {
        if (this.id === "period-content-" + tabName) {
            this.classList.remove("d-none");
        } else {
            this.classList.add("d-none");
        }
    });
    $(".period-tab").each(function () {
        if (this.id === tab.id) {
            this.classList.add("active");
        } else {
            this.classList.remove("active");
        }
    });
}
