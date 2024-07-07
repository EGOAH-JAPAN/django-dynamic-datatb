export let myData = {}
export let modelName = ''

export const setData = (headings, displayHeadings, data, fieldTypes) => {
    myData = {
        headings: headings,
        displayHeadings: displayHeadings,
        data: data,
        fieldTypes: fieldTypes,
    }
}

export const setModelName = (data) => {
    modelName = data
}