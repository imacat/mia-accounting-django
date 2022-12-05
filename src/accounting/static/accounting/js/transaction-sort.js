/* The Mia Website
 * sort.js: The JavaScript to reorder the transactions
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
 * First written: 2019/10/13
 */

// Initializes the page JavaScript.
$(function () {
    $("#transactions").sortable({
        classes: {
            "ui-sortable-helper": "table-active",
        },
        cursor: "move",
        stop: function () {
            resetTransactionOrders();
        },
    });
});

/**
 * Resets the order of the transactions according to their appearance.
 *
 * @private
 */
function resetTransactionOrders() {
    const sorted = $("#transactions").sortable("toArray");
    for (let i = 0; i < sorted.length; i++) {
        $("#" + sorted[i] + "-ord")[0].value = i + 1;
    }
}
