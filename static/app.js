const itemsByCode = new Map();

const tbody = document.querySelector("#linesTable tbody");
tbody.addEventListener("change", (event) => {

    const item = itemsByCode.get(event.target.value);

    if (item) {
        loadLineItem(item);
    }
})

async function clean() {
    const text = document.getElementById("emailInput").value;
    document.getElementById("cleanedText").value = ""; // placeholder

    const res = await fetch("/clean", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            id: window.currentID,
            email: text
        })
    });
    const data = await res.json();

    document.getElementById("cleanedText").value = data.body;
}

async function extract() {
    const text = document.getElementById("emailInput").value;

    const res = await fetch("/extract", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            id: window.currentID,
            email: text
        })
    });
    const data = await res.json();
    
    document.getElementById("azienda").value = data.azienda || "";
    document.getElementById("paese").value = data.paese || "";
    document.getElementById("email").value = data.email || "";
    document.getElementById("contatto").value = data.contatto || "";
    document.getElementById("telefono").value = data.telefono || "";
    document.getElementById("articolo").value = data.articolo || "";
    document.getElementById("marca").value = data.marca || "";
    document.getElementById("qta").value = data.qta || "";
    document.getElementById("note").value = data.note || "";

}

async function proceedToWeb() {
    const text = document.getElementById("cleanedText").value;

    const res = await fetch("/websearch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            id: window.currentID,
            email: text
        })
    })
    const dataResponse = await res.json();
    const clean = dataResponse.llm_response
        .replace(/```json/g, "")
        .replace(/```/g, "")
        .trim();
    
    try {
        
        const data = JSON.parse(clean);
        const extractedItems = data.items;
        let searchItems = [...extractedItems];

        if (searchItems.length === 1 && !searchItems[0].item_code && searchItems[0].description_source == "email") {
            searchItems = await extractDescription(text)
        }

        // clear previous rows
        tbody.innerHTML = "";

        // populate candidates
        searchItems.forEach((item, index) => {
            const row = document.createElement("tr");
            const key = item.item_code || `item-${index}`;
            
            row.innerHTML = `
            <td>${item.item_code || "-"}</td>
            <td>${item.description}</td>
            <td>
                <input
                    type="radio"
                    name="itemSelect"
                    value="${key}"
                >
            </td>
        `;
            itemsByCode.set(key, item);
            tbody.appendChild(row);
        });
        
    } catch (err) {
        console.error("Invalid JSON:", err);
        alert("The LLM Response field does not contain valid JSON.");
    }

}

async function loadLineItem(item) {

    document.getElementById("articolo").value = item.item_code || "";
    document.getElementById("marca").value = item.brand || "";
    document.getElementById("qta").value = item.quantity || "";
    document.getElementById("note").value = item.description || "";

}

async function searchCode() {
    item_code = document.getElementById("articolo").value;
    description = document.getElementById("note").value;
    if (!item_code && !description) return;
    let res;

    if (item_code) {
        res = await fetch(
            `/search_code?q=${encodeURIComponent(item_code)}`,
            {
                method: "GET"
            }
        );

    } else {
            description = document.getElementById("note").value;
            res = await fetch("/find_embeddings", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    id: window.currentID,
                    description: description
                })
            }
        )
    }
    
    const data = await res.json();
    // devo ricevere i candidati a questo punto

    if (data.length === 0) {
        alert("No candidates found");
        return
    }

    // show original searched code
    document.getElementById("companyCode").textContent = data.required_code;
    const tbody = document.querySelector("#candidateTable tbody");

    // clear previous rows
    tbody.innerHTML = "";

    // populate candidates
    data.forEach((candidate, index) => {
        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${candidate.required_code}</td>
            <td>${candidate.inner_code}</td>
            <td>${candidate.description || ""}</td>
            <td>${candidate.score}</td>
            <td>
                <input
                    type="radio"
                    name="candidateSelect"
                    value="${candidate.inner_code}"
                    ${index === 0 ? "checked" : ""}
                >
            </td>
        `;
        tbody.appendChild(row);
    });

    // show popup
    document.getElementById("reviewSection").classList.remove("hidden");
}

async function loadNext() {
    
    if (!document.getElementById("detailPanel").classList.contains("hidden")) {
        document.getElementById("detailPanel").classList.add("hidden")
    }
    if (!document.getElementById("reviewSection").classList.contains("hidden")) {
        document.getElementById("reviewSection").classList.add("hidden")
    }

    document.getElementById("cleanedText").value = "";
   
    document.getElementById("azienda").value = "";
    document.getElementById("paese").value = "";
    document.getElementById("email").value = "";
    document.getElementById("contatto").value = "";
    document.getElementById("telefono").value = "";
    document.getElementById("articolo").value = "";
    document.getElementById("marca").value = "";
    document.getElementById("qta").value = "";
    document.getElementById("note").value = "";
    const res = await fetch("/next");
    const data = await res.json();


    document.getElementById("giac1").value = '0'
    document.getElementById("giac2").value = '0'
    document.getElementById("giac3").value = '0'
    document.getElementById("giac4").value = '0'

    document.getElementById("allInt1").value = '0'
    document.getElementById("allInt2").value = '0'
    document.getElementById("allInt3").value = '0'
    document.getElementById("allInt4").value = '0'

    document.getElementById("allGlo1").value = '0'
    document.getElementById("allGlo2").value = '0'
    document.getElementById("allGlo3").value = '0'
    document.getElementById("allGlo4").value = '0'

    document.getElementById("ordFor1").value = '0'
    document.getElementById("ordFor2").value = '0'
    document.getElementById("ordFor3").value = '0'
    document.getElementById("ordFor4").value = '0'

    document.getElementById("ordCli1").value = '0'
    document.getElementById("ordCli2").value = '0'
    document.getElementById("ordCli3").value = '0'
    document.getElementById("ordCli4").value = '0'

    document.getElementById("discount1").value = '0'
    document.getElementById("discount2").value = '0'
    document.getElementById("discount3").value = '0'
    document.getElementById("aumento1").value = '0'
    document.getElementById("aumento2").value = '0'
    document.getElementById("netPrice").value = ""
    document.getElementById("grossPrice").value = ""
    document.getElementById("description").value = ""
    document.getElementById("grpscoven").value = ""

    document.getElementById("replyBox").value="";

    if (data.status === "done") {
        document.getElementById("emailInput").value = "";
        alert("All emails processed!")
        return;
    }

    document.getElementById("emailInput").value = data.email;
    // document.getElementById("output").value = "";  // 👈 IMPORTANT
    window.currentID = data.id;

    // clear previous rows
    tbody.innerHTML = "";
}

async function skip() {

    await fetch("/skip", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            id: window.currentID,
            email: "skip"
        })
    });
    loadNext();
}

async function openDetailPanel(innerCode) {
    document.getElementById("innerCode").value = innerCode
    document.getElementById("replyAddress").value = document.getElementById("email").value
    document.getElementById("1").value = "SITO 1"
    document.getElementById("2").value = "SITO 2"
    document.getElementById("3").value = "SITO 3"
    document.getElementById("4").value = "SITO 4"
    


    const res = await fetch(`/get_details_demo?codmat=${encodeURIComponent(innerCode)}`,
        {
            method: "GET"
        });

    const data = await res.json();
    
    document.getElementById("disp1").value = data.qtaDispo1 || '0'
    document.getElementById("disp2").value = data.qtaDispo2 || '0'
    document.getElementById("disp3").value = data.qtaDispo3 || '0'
    document.getElementById("disp4").value = data.qtaDispo4 || '0'

    document.getElementById("giac1").value = data.giac1 || '0'
    document.getElementById("giac2").value = data.giac2 || '0'
    document.getElementById("giac3").value = data.giac3 || '0'
    document.getElementById("giac4").value = data.giac4 || '0'

    document.getElementById("allInt1").value = data.allInt1 || '0'
    document.getElementById("allInt2").value = data.allInt2 || '0'
    document.getElementById("allInt3").value = data.allInt3 || '0'
    document.getElementById("allInt4").value = data.allInt4 || '0'

    document.getElementById("allGlo1").value = data.allGlo1 || '0'
    document.getElementById("allGlo2").value = data.allGlo2 || '0'
    document.getElementById("allGlo3").value = data.allGlo3 || '0'
    document.getElementById("allGlo4").value = data.allGlo4 || '0'

    document.getElementById("ordFor1").value = data.ordFor1 || '0'
    document.getElementById("ordFor2").value = data.ordFor2 || '0'
    document.getElementById("ordFor3").value = data.ordFor3 || '0'
    document.getElementById("ordFor4").value = data.ordFor4 || '0'

    document.getElementById("ordCli1").value = data.ordCli1 || '0'
    document.getElementById("ordCli2").value = data.ordCli2 || '0'
    document.getElementById("ordCli3").value = data.ordCli3 || '0'
    document.getElementById("ordCli4").value = data.ordCli4 || '0'

    document.getElementById("discount1").value = data.SCO1 || '0' 
    document.getElementById("discount2").value = data.SCO2 || '0'
    document.getElementById("discount3").value = data.SCO3 || '0'
    document.getElementById("aumento1").value = data.AUM1 || '0'
    document.getElementById("aumento2").value = data.AUM2 || '0'
    document.getElementById("netPrice").value = data.pzoNetto
    document.getElementById("grossPrice").value = data.pzoLordo
    document.getElementById("description").value = data.desc || ""
    document.getElementById("grpscoven").value = data.grpscoven || ""

    document.getElementById("detailPanel").classList.remove("hidden");
}

async function sendReply() {
    //const email = document.getElementById("emailInput").value;
    //const edited_email = document.getElementById("cleanedText").value;
    //const llm_response = document.getElementById("llmResponse").value;
    //const required_code = document.getElementById("articolo").value;
    //const supplier_code = document.getElementById("articolo").value;
    //const inner_code = document.getElementById("innerCode").value;
    //const marca = document.getElementById("marca").value;
    //const reply = document.getElementById("replyBox").value;
    //const reply_address = document.getElementById("replyAddress").value;

    const res = await fetch("/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
              id: parseInt(window.currentID),
              original_email: email || "",
              web_email: edited_email || "",
              llm_response: llm_response || "",
              required_code: required_code || "",
              supplier_code: supplier_code || "",
              inner_code: inner_code || "",
              required_brand: marca || "",
              email_response: reply || "",
              reply_address: reply_address || ""
        })
    })

    //const data = await res.json();

    alert("E-mail successfully sent");

    loadNext();
}
function selectItem() {
    const selected = document.querySelector(
        'input[name="candidateSelect"]:checked'
    )
    if (!selected) {
        alert("Select a candidate");
        return;
    }
    const innerCode = selected.value;
    
    // Example:
    
    // Hide popup
    closeReviewModal();

    openDetailPanel(innerCode);

}
function closeReviewModal() {
    document
        .getElementById("reviewSection")
        .classList.add("hidden");
}
function closeDetailPanel() {
    document.getElementById("detailPanel").classList.add("hidden");
}
async function extractDescription(text) {
    const res = await fetch("/extractDescription", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            id: window.currentID,
            email: text
        })
    })
    const data = await res.json();
    const clean = data.llm_response
        .replace(/```json/g, "")
        .replace(/```/g, "")
        .trim();
    try {

        const data = JSON.parse(clean);
        return data.items;

    }
    catch {
        console.error("Invalid JSON:", err);
        alert("The LLM Response field does not contain valid JSON.");
        return null;
    }
}

document.addEventListener("DOMContentLoaded", function () {
    loadNext();
    startTour();
});

const tourSteps = [
    {
        element: "#emailPanel",
        title: "Start with the customer email",
        text:
            "Paste the customer's inquiry here or let it flow directly from your email box. " +
            "The application can work with unstructured emails " +
            "and extract the product information needed for the catalog search."
    },
    {
        element: "#extractBtn",
        title: "Extract from pre-formatted emails",
        text:
            "If you receive pre-formatted inquiries, " +
            "you can link a set of reg-ex to this button " +
            "and extract all the required fields."
    },
    {
        element: "#cleanBtn",
        title: "Protect confidential information",
        text:
            "Otherwise you can submit the text to an LLM. " +
            "Before you do that, make sure to clear the text from confidential information " +
            "such as signature, telephone number, VAT number etc."
    },
    {
        element: "#clearedText",
        title: "Submit the text to generative AI",
        text:
            "The LLM is prompted to search for " +
            "lines of a customer inquiry: " +
            "code, description, quantity etc."
    },
    {
        element: "#offerLines",
        title: "Table containing the list of requested items",
        text:
            "By selecting a row " +
            "the corresponding data will be loaded " +
            "in the \"Extracted Data\" form"
    },
    {
        element: "#extractedData",
        title: "Match the email code with your company code",
        text:
            "When you press the button, " +
            "If a product code is available, the catalog is searched directly. " +
            "Otherwise, the description is used for semantic matching. " +
            "Product descriptions are converted into embeddings and compared against the PostgreSQL catalog using pgvector."
    }
];

let currentTourStep = 0;

window.addEventListener("resize", function () {
    const step = tourSteps[currentTourStep];

    if (!step) return;
    const element = document.querySelector(step.element);
    if (!element) return;

    requestAnimationFrame(() => {
        positionTourCard(element);
    });

});

window.addEventListener("scroll", function () {
    const step = tourSteps[currentTourStep];

    if (!step) return;
    const element = document.querySelector(step.element);

    if (element) {
        positionTourCard(element);
    }

});
function startTour() {
    currentTourStep = 0;

    document
        .getElementById("tourOverlay")
        .classList.add("active");

    document
        .getElementById("tourCard")
        .classList.add("active");

    showTourStep();
}

function showTourStep() {

    // Remove previous highlight
    document
        .querySelectorAll(".tour-highlight")
        .forEach(el => el.classList.remove("tour-highlight"));

    const step = tourSteps[currentTourStep];

    const element = document.querySelector(step.element);

    if (!element) {
        console.error("Tour element not found:", step.element);
        return;
    }

    element.classList.add("tour-highlight");

    // Update card
    document.querySelector(".tour-step").textContent =
        `${currentTourStep + 1} / ${tourSteps.length}`;

    document.querySelector(".tour-card h3").textContent =
        step.title;

    document.querySelector(".tour-card p").textContent =
        step.text;

    // Put the card underneath the highlighted element
    positionTourCard(element);
}

function positionTourCard(element) {

    const card = document.getElementById("tourCard");
    const rect = element.getBoundingClientRect();

    const margin = 20;
    const gap = 16;

    const cardWidth = card.offsetWidth;
    const cardHeight = card.offsetHeight;

    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    let left;
    let top;

    /*
     * 1. Try BELOW the element
     */
    left = rect.left + (rect.width - cardWidth) / 2;
    top = rect.bottom + gap;

    if (
        top + cardHeight <= viewportHeight - margin &&
        left >= margin &&
        left + cardWidth <= viewportWidth - margin
    ) {
        setCardPosition(left, top);
        return;
    }

    /*
     * 2. Try ABOVE the element
     */
    left = rect.left + (rect.width - cardWidth) / 2;
    top = rect.top - cardHeight - gap;

    if (
        top >= margin &&
        left >= margin &&
        left + cardWidth <= viewportWidth - margin
    ) {
        setCardPosition(left, top);
        return;
    }

    /*
     * 3. Try RIGHT
     */
    left = rect.right + gap;
    top = rect.top + (rect.height - cardHeight) / 2;

    if (
        left + cardWidth <= viewportWidth - margin &&
        top >= margin &&
        top + cardHeight <= viewportHeight - margin
    ) {
        setCardPosition(left, top);
        return;
    }

    /*
     * 4. Try LEFT
     */
    left = rect.left - cardWidth - gap;
    top = rect.top + (rect.height - cardHeight) / 2;

    if (
        left >= margin &&
        top >= margin &&
        top + cardHeight <= viewportHeight - margin
    ) {
        setCardPosition(left, top);
        return;
    }

    /*
     * 5. Nothing fits perfectly.
     *    Put it below and constrain it to the viewport.
     */
    left = Math.max(
        margin,
        Math.min(
            left,
            viewportWidth - cardWidth - margin
        )
    );

    top = Math.max(
        margin,
        Math.min(
            rect.bottom + gap,
            viewportHeight - cardHeight - margin
        )
    );

    setCardPosition(left, top);
}


function setCardPosition(left, top) {

    const card = document.getElementById("tourCard");

    card.style.left = `${left}px`;
    card.style.top = `${top}px`;
}

function nextTourStep() {

    if (currentTourStep >= tourSteps.length - 1) {
        endTour();
        return;
    }

    currentTourStep++;

    showTourStep();
}

function skipTour() {
    endTour();
}

function endTour() {

    document
        .querySelectorAll(".tour-highlight")
        .forEach(el => el.classList.remove("tour-highlight"));

    document
        .getElementById("tourOverlay")
        .classList.remove("active");

    document
        .getElementById("tourCard")
        .classList.remove("active");
}