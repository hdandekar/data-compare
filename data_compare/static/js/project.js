
// Adds toast on events of changes
document.addEventListener('DOMContentLoaded', () => {
    const toast = document.getElementById("toast");
    const toastElement = document.getElementById("notification")
    const server_message = document.getElementById("server_message");
    // const toast = new bootstrap.Toast(toastElement, { delay: 10000 })
    htmx.on("showMessage", (e) => {
        toast.removeAttribute("hidden");
        server_message.innerText = e.detail.value
    })

    htmx.on("errors", (e) => {
        console.log("errors are", e)
    })

    // Change the toast class based on eventType
    htmx.on("eventType", (e) => {
        if (['created', 'updated',].includes(e.detail.value)) {
            toastElement.classList.add("is-success");
        } else if (['deleted'].includes(e.detail.value)) {
            toastElement.classList.add("is-danger");
        }
        else if (['triggerd'].includes(e.detail.value)) {
            toastElement.classList.remove('is-danger', 'is-success', 'is-warning');
            toastElement.classList.add("is-warning")
        }
    })

    htmx.on("removeTCListForm", (e) => {
        if (e.detail.value === 'True') {
            element = document.getElementById("testcase_list")
            element.innerHTML = '';
        }

    })

    htmx.on("removeTCListForm", (e) => {
        if (e.detail.value === 'True') {
            element = document.getElementById("testcase_list")
            element.innerHTML = '';
        }

    })
});


// To close the toast messages
document.addEventListener('DOMContentLoaded', () => {
    const button = document.querySelector('.notification .delete');
    button.addEventListener('click', () => {
        button.parentNode.parentElement.setAttribute("hidden","")
        cls_list = Array.from(button.parentElement.classList)
        cls_list.forEach(cls => {
            if(cls !== 'notification' ) {
                button.parentElement.classList.remove(cls);
            }
        })
    });
});


// document.addEventListener('DOMContentLoaded', () => {
//     const button = document.querySelector('#msgClose');
//     button.addEventListener('click', () => {
//         button.remove();
//     });
// });

// document.addEventListener('DOMContentLoaded', () => {
//     const clsBtn = document.getElementById('msgClose');
//     clsBtn.addEventListener('click', () => {
//         cls.Btn.parentElement.remove();
//     })
// });

document.addEventListener('DOMContentLoaded', () => {
    const clsBtn = document.getElementById('msgClose');
    if (clsBtn) {
        clsBtn.addEventListener('click', () => {
            clsBtn.parentElement.remove();
        });
    }
});


// To close modal on clicking outside modal's visible area.
document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('modal');
    htmx.on("htmx:afterSwap", (e) => {
        // Response targeting #dialog => show the modal
        if (e.detail.target.id == "dialog") {
            modal.classList.add('is-active');
            const modalBackground = modal.querySelector('.modal-background');
            if (modalBackground) {
                modalBackground.addEventListener('click', () => {
                    modal.classList.remove('is-active');
                });
            }
            else {
                console.error('Modal background not found after swap.');
            }
        }
    });
    htmx.on("htmx:beforeSwap", (e) => {
        // Empty response targeting #dialog => hide the modal
        if (e.detail.target.id == "dialog" && !e.detail.xhr.response) {
            modal.classList.remove('is-active')
            // modal.hide()
            e.detail.shouldSwap = false
        }
    })
});

    // document.getElementById('toggle-button').addEventListener('click', function() {
    //     document.getElementById('side-section').classList.add('is-active');
    // });
    // document.getElementById('close-button').addEventListener('click', function() {
    //     document.getElementById('side-section').classList.remove('is-active');
    // });
