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
    console.log("Extract data");
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
    console.log(data);

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
    const data = await res.json();
    const clean = data.llm_response
        .replace(/```json/g, "")
        .replace(/```/g, "")
        .trim();
    console.log(clean);

    try {
        
        const data = JSON.parse(clean);


        const tbody = document.querySelector("#linesTable tbody");

        // clear previous rows
        tbody.innerHTML = "";

        // populate candidates
        data.items.forEach((item, index) => {
            const row = document.createElement("tr");

            console.log(`Desc: ${item.description}`)

            row.innerHTML = `
            <td>${item.item_code}</td>
            <td>${item.description}</td>
        `;
            tbody.appendChild(row);
        });



        //const item = data.items?.[0] || {};

        //console.log("Retrieved from AI: " + data.items?.[0]);

        //document.getElementById("articolo").value = item.item_code || "";
        //document.getElementById("marca").value = item.brand || "";
        //document.getElementById("qta").value = item.quantity || "";
        //document.getElementById("note").value = item.description || "";
    } catch (err) {
        console.error("Invalid JSON:", err);
        alert("The LLM Response field does not contain valid JSON.");
    }

}

async function searchCode() {
    item_code = document.getElementById("articolo").value;

    const res = await fetch(
        `/search_code?q=${encodeURIComponent(item_code)}`,
        {
            method: "GET"
        }
    );

    const data = await res.json();
    // devo ricevere i candidati a questo punto
    console.log("Search inner code:");
    console.log(data)

    if (data.status !== "review") {
        alert("No candidates found");
        return
    }

    // show original searched code
    document.getElementById("companyCode").textContent = data.required_code;
    const tbody = document.querySelector("#candidateTable tbody");

    // clear previous rows
    tbody.innerHTML = "";

    // populate candidates
    data.candidates.forEach((candidate, index) => {
        const row = document.createElement("tr");

        console.log(`Desc: ${candidate.description}`)

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
    // console.log("LOADNEXT START");

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

    // console.log("LOADNEXT DATA:", data);

    if (data.status === "done") {
        console.log("NO MORE EMAILS");
        document.getElementById("emailInput").value = "";
        // document.getElementById("output").value = "";
        alert("All emails processed!")
        return;
    }

    document.getElementById("emailInput").value = data.email;
    // document.getElementById("output").value = "";  // 👈 IMPORTANT
    window.currentID = data.id;
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
    console.log("CALLING loadNext AFTER SKIP");
    loadNext();
}

async function openDetailPanel(innerCode) {
    console.log(`Showing side-panel: ${innerCode}`);
    document.getElementById("innerCode").value = innerCode
    document.getElementById("replyAddress").value = document.getElementById("email").value
    document.getElementById("vrz").value = "VERZOLLA"
    document.getElementById("amati").value = "AMATI"
    document.getElementById("como").value = "COMO"
    document.getElementById("civate").value = "CIVATE"


    const res = await fetch(`/get_details?codmat=${encodeURIComponent(innerCode)}`,
        {
            method: "GET"
        });

    const data = await res.json();
    console.log(data);

    document.getElementById("dispVrz").value = data.qtaDispoVrz
    document.getElementById("dispAma").value = data.qtaDispoAma
    document.getElementById("dispCo").value = data.qtaDispoCo
    document.getElementById("dispCv").value = data.qtaDispoCv

    document.getElementById("giacVrz").value = data.giacVrz
    document.getElementById("giacAma").value = data.giacAma
    document.getElementById("giacCo").value = data.giacCo
    document.getElementById("giacCv").value = data.giacCv

    document.getElementById("allIntVrz").value = data.allIntVrz
    document.getElementById("allIntAma").value = data.allIntAma
    document.getElementById("allIntCo").value = data.allIntCo
    document.getElementById("allIntCv").value = data.allIntCv

    document.getElementById("allGloVrz").value = data.allGloVrz
    document.getElementById("allGloAma").value = data.allGloAma
    document.getElementById("allGloCo").value = data.allGloCo
    document.getElementById("allGloCv").value = data.allGloCv

    document.getElementById("ordForVrz").value = data.qtaOrdForVrz
    document.getElementById("ordForAma").value = data.qtaOrdForAma
    document.getElementById("ordForCo").value = data.qtaOrdForCo
    document.getElementById("ordForCv").value = data.qtaOrdForCv

    document.getElementById("ordCliVrz").value = data.ordCliVrz
    document.getElementById("ordCliAma").value = data.ordCliAma
    document.getElementById("ordCliCo").value = data.ordCliCo
    document.getElementById("ordCliCv").value = data.ordCliCv

    document.getElementById("discount1").value = data.SCO1
    document.getElementById("discount2").value = data.SCO2
    document.getElementById("discount3").value = data.SCO3
    document.getElementById("aumento1").value = data.AUM1
    document.getElementById("aumento2").value = data.AUM2
    document.getElementById("netPrice").value = data.pzoNetto
    document.getElementById("grossPrice").value = data.pzoLordo
    document.getElementById("description").value = data.desc1 + " - " + data.desc2 + "   " + data.desc3
    document.getElementById("grpscoven").value = data.grpscoven

    document.getElementById("detailPanel").classList.remove("hidden");
}

async function sendReply() {
    const email = document.getElementById("emailInput").value;
    const edited_email = document.getElementById("cleanedText").value;
    const llm_response = document.getElementById("llmResponse").value;
    const required_code = document.getElementById("articolo").value;
    const supplier_code = document.getElementById("articolo").value;
    const inner_code = document.getElementById("innerCode").value;
    const marca = document.getElementById("marca").value;
    const reply = document.getElementById("replyBox").value;
    const reply_address = document.getElementById("replyAddress").value;
    
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

    const data = await res.json();
    console.log("SERVER RESPONSE: ", data);

    loadNext();
}
function selectItem() {
    const selected = document.querySelector(
        'input[name="candidateSelect"]:checked'
    )
    console.log(selected);
    if (!selected) {
        alert("Select a candidate");
        return;
    }
    const innerCode = selected.value;
    console.log("Selected:", innerCode);

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

document.addEventListener("DOMContentLoaded", function () {
    loadNext();
});