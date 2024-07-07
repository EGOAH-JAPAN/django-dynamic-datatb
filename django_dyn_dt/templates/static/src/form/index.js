import { myData } from '../../data/index.js';

export const formTypes = {
    ADD: 'add',
    EDIT: 'edit',
    DELETE: 'delete',
};

export const formConstructor = (formType, item) => {
    const form = document.getElementById('form');
    form.className = 'd-flex flex-column gap-1 p-3';
    form.innerHTML = '';
    
    myData.headings.forEach((d, i) => {
        const label = document.createElement('label');
        label.setAttribute('htmlFor', i);
        label.innerHTML = myData.displayHeadings[i];
        label.className = 'form-label m-0';

        let input;
        
        switch (myData.fieldTypes[i]) {
            case 'date':
                input = document.createElement('input');
                input.setAttribute('type', 'date');
                break;
            case 'integer':
                input = document.createElement('input');
                input.setAttribute('type', 'number');
                input.setAttribute('step', '1');
                break;
            case 'float':
                input = document.createElement('input');
                input.setAttribute('type', 'number');
                input.setAttribute('step', 'any');
                break;
            case 'boolean':
                input = document.createElement('input');
                input.setAttribute('type', 'checkbox');
                break;
            default:
                input = document.createElement('input');
                input.setAttribute('type', 'text');
                break;
        }
        
        input.className = 'form-control m-0';
        input.placeholder = d;
        
        if (d === 'id' || formType === formTypes.DELETE) {
            input.setAttribute('disabled', 'true');
        }

        if (formType !== formTypes.ADD && myData.fieldTypes[i] !== 'boolean') {
            input.setAttribute('value', item[i]);
        }

        if (formType !== formTypes.ADD && myData.fieldTypes[i] === 'boolean') {
            input.checked = item[i] === 'true';
        }

        form.appendChild(label);
        form.appendChild(input);

        // Add an empty div for error messages
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        form.appendChild(errorDiv);
    });

    if (formType === formTypes.ADD) {
        document.querySelector('.modal-title').innerHTML = '登録';
        document.querySelector('.modal-btn').value = '登録';
    } else if (formType === formTypes.EDIT) {
        document.querySelector('.modal-title').innerHTML = '編集';
        document.querySelector('.modal-btn').value = '編集';
    } else if (formType === formTypes.DELETE) {
        document.querySelector('.modal-title').innerHTML = '削除';
        document.querySelector('.modal-btn').value = '削除';
    }

    return form;
};
