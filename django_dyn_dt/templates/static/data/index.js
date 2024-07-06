export let myData = {}
export let modelName = ''

export const setData = (headings, displayHeadings, data, isDate) => {
    myData = {
        headings: headings,
        displayHeadings: displayHeadings,
        data: data,
        isDate: isDate,
    }
}

export const setModelName = (data) => {
    modelName = data
}