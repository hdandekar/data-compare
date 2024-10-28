; (function () {
    const toastElement = document.getElementById("toast")
    const toastBody = document.getElementById("toast-body")
    const toast = new bootstrap.Toast(toastElement, { delay: 10000 })
    htmx.on("showMessage", (e) => {
        toastBody.innerText = e.detail.value
        toast.show()
    })

    htmx.on("errors", (e) => {
        console.log("errors are", e)
    })

    // Change the toast class based on eventType
    htmx.on("eventType", (e) => {
        if (['created', 'updated',].includes(e.detail.value)) {
            toastElement.classList.remove('bg-danger', 'bg-success');
            toastElement.classList.add("bg-success");
        } else if (['deleted'].includes(e.detail.value)) {
            toastElement.classList.remove('bg-danger', 'bg-success');
            toastElement.classList.add("bg-danger");
        }
        else if (['triggerd'].includes(e.detail.value)) {
            toastElement.classList.remove('bg-danger', 'bg-success', 'bg-warning');
            toastElement.classList.add("bg-warning")
        }
    })

    htmx.on("removeTCListForm", (e) => {
        if (e.detail.value === 'True') {
            element = document.getElementById("testcase_list")
            element.innerHTML = '';
        }

    })
})();
