/* The Mia Website
 * regular-payments.js: The JavaScript for the regular payments
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
 * First written: 2020/4/4
 */

/**
 * Returns the regular payment data.
 *
 * @returns {{debit: [], credit: []}}
 */
function getRegularPayments() {
    const today = new Date($("#txn-date").get(0).value);
    const thisMonth = today.getMonth() + 1;
    const lastMonth = (thisMonth + 10) % 12 + 1;
    let regular = {
        debit: [],
        credit: [],
    };
    regular.debit.push({
        title: "共同生活基金",
        summary: "共同生活基金" + thisMonth + "月",
        account: "62651",
    });
    regular.debit.push({
        title: "電話費",
        summary: "電話費" + lastMonth + "月",
        account: "62562",
    });
    regular.debit.push({
        title: "健保",
        summary: "健保" + lastMonth + "月",
        account: "62621",
    });
    regular.debit.push({
        title: "國民年金",
        summary: "國民年金" + lastMonth + "月",
        account: "13141",
    });
    regular.credit.push({
        title: "薪水",
        summary: lastMonth + "月份薪水",
        account: "46116",
    });
    return regular;
}
