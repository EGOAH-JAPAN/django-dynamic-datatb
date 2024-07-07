import {modelName, myData} from '../data/index.js'
import {events} from './events/index.js'
import {
    removeRow,
    addRow,
    editRow,
    search,
    columnsManage,
    exportController, 
    addController,
    middleContainer,
} from './controller/index.js'
import { formConstructor, formTypes } from './form/index.js'

let formType = formTypes.ADD

// table
console.log(myData)
const dataTable = new simpleDatatables.DataTable('table' , {
    data: {
        headings: myData.displayHeadings,
        data: myData.data
    },
    perPageSelect: [10,25,50],
    perPage: parseInt(new URLSearchParams(window.location.search).get('entries')) || 10,
    labels: {
        placeholder: "Search...",
        perPage: "{select} 件/ページ",
        noRows: "データは見つかりませんでした。",
        // info: "Showing {start} to {end} of {rows} entries",
        info: "{rows} 件中 {start}~{end} 件を表示",
    },
    searchable: false,
})

// edit & remove Button
const newColumn = []
myData.data.forEach((d,i) => {

    const editBtn = `<i class="btn-outline-primary edit bi bi-pencil-square" data-bs-toggle="modal" data-bs-target="#exampleModal"></i>`
    
    const removeBtn = `<i class="btn-outline-danger remove bi bi-eraser"></i>`;

    newColumn.push(editBtn + " &nbsp; " + removeBtn)
})
        // add buttons
dataTable.columns().add({
    heading: '',
    data: newColumn
})
        // add funcs
dataTable.table.addEventListener('click', (e) => {
    if (e.target.nodeName === 'I') {
        const row = e.target.closest('tr');
        if (e.target.className.includes('remove')) {
            if (confirm("削除します。よろしいですか")) {
                removeRow(dataTable, row.dataIndex);
            }
        } else if (e.target.className.includes('edit')) {
            const rowContent = [].slice.call(dataTable.data[row.dataIndex].cells).map((cell) => { return cell.textContent; });
            formType = formTypes.EDIT;
            formConstructor(formTypes.EDIT, rowContent);
        }
    }
});

window.onload = () => {
    if (sessionStorage.getItem('register') == null)
        localStorage.removeItem('hideColumns');

    sessionStorage.setItem('register', 1);

    const hideColumns = JSON.parse(localStorage.getItem('hideColumns'))
    hideColumns.forEach(d => {
        dataTable.columns().hide([myData.headings.indexOf(d)])
    })

    const els = document.getElementsByClassName('form-check-input')
    Array.prototype.forEach.call(els, function(el) {
        if (hideColumns.includes(el.id)) {
            el.checked = true
        }
    });
}

// events
events(dataTable)

// To be coded
//middleContainer(dataTable)

// columns manage
columnsManage(dataTable)

// add
addController(formType)

// export
exportController(dataTable)

// Search Box
search()

document.addEventListener('submit', (e) => {
    e.preventDefault();
    const formData = getFormData();

    if (formType === formTypes.ADD) {
        addRow(dataTable, formData);
    } else if (formType === formTypes.EDIT) {
        editRow(dataTable, formData);
    }
});

const getFormData = () => {
    const data = {};
    const myForm = document.querySelector('form');

    for (let i of myForm.elements) {
        if (i.type === 'text' || i.type === 'date') {
            data[i.placeholder] = i.value;
        }
    }

    return data;
};

const displayErrors = (errors) => {
    for (const [field, message] of Object.entries(errors)) {
        const input = document.querySelector(`input[placeholder='${field}']`);
        if (input) {
            input.classList.add('is-invalid');
            const errorDiv = document.createElement('div');
            errorDiv.className = 'invalid-feedback';
            errorDiv.innerText = message.join(', ');
            input.parentNode.appendChild(errorDiv);
        }
    }
};

// style
// modelName
// document.querySelector('.model-name').innerHTML = modelName
document.querySelector('.dataTable-top').className += ' d-flex justify-content-between'
