
document.getElementById("generate-sql-button").addEventListener("click", async function () {

    updateSQLBox({ filter_clause: "" }); 
    const dataParagraph = document.querySelector("#audience-data .data-content p");
    dataParagraph.textContent = "";
    resetDataSources(); 
    const questionInput = document.getElementById("question");
    const attributeGoal = questionInput.value.trim();
    if (!attributeGoal) return;
  
   const loadingIndicator = document.getElementById("loading-indicator");
    const progressMsg = document.getElementById("progress-messages");
    document.querySelector(".query-feedback-buttons").classList.add("hidden");
    loadingIndicator.classList.remove("hidden");

    // Stream messages
    const messages = [
        "Submitting the user input...",
        "Reviewing the dataset schema...",
        "Identifying relevant columns and filter logic...",
        "Generating the audience insights..."
    ];

    let msgIndex = 0;
    progressMsg.textContent = messages[msgIndex];
    msgIndex++;

    const messageInterval = setInterval(() => {
        if (msgIndex < messages.length) {
            progressMsg.textContent = messages[msgIndex];
            msgIndex++;
        } else {
            clearInterval(messageInterval);
        }
    }, 3000);

    // Clear previous generated attribute
    const explanationSection = document.querySelector("#attribute-explanation-section .explanation-content p");
    explanationSection.innerHTML = "";

    try {
        // Call backend API
        const response = await fetch("/submit_question/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ attribute_goal: attributeGoal })
        });

        const result = await response.json();

       if (result.success) {
            const attributeName = result.attribute_name || "";
            const attributeDescription = result.attribute_description || "No description generated.";

            window.attributeGoal = attributeGoal;
            window.filterClause = result.filter_clause || "";
            window.columnsUsed = result.columns_used || [];

            // Clear previous content
            explanationSection.innerHTML = "";

            // Add Attribute Name
            const nameEl = document.createElement("strong");
            nameEl.textContent = attributeName;
            explanationSection.appendChild(nameEl);

            // Create the inner card dynamically
            const innerCard = document.createElement("div");
            innerCard.className = "card description-card";
            innerCard.style.marginTop = "10px"; 
            innerCard.style.backgroundColor = "#f9f9f9";
            innerCard.style.border = "1px solid #d9d0d0";

            // Add description text
            const descEl = document.createElement("p");
            descEl.textContent = attributeDescription;
            innerCard.appendChild(descEl);

            // Add the inner card below the name
            explanationSection.appendChild(innerCard);
          

        } else {
            explanationSection.innerHTML = `Error: ${result.error || "Failed to generate attribute."}`;
        }
        updateDataBox(result)
        updateDataSources(result);
        updateSQLBox(result);
        
        // Show feedback buttons after generation
        document.querySelector(".query-feedback-buttons").classList.remove("hidden");
        const feedbackMsg = document.getElementById("feedback-message");
        feedbackMsg.textContent = "";
    } catch (err) {
        explanationSection.innerHTML = `Error: ${err.message}`;
    } finally {
        // Hide loading indicator
        loadingIndicator.classList.add("hidden");
    }
});

function updateDataSources(data) {
    resetDataSources();
    const container = document.querySelector(".data-sources-grid");
    container.innerHTML = "";

    if (!data.columns_used || data.columns_used.length === 0) {
        container.innerHTML = "<p>No columns used in this query.</p>";
        return;
    }

    // Create a single card for all columns since we have only one table
    const card = document.createElement("div");
    card.className = "data-card";

    // Inner div
    const inner = document.createElement("div");
    inner.className = "card-inner";

    // Card heading
    const h4 = document.createElement("h4");
    h4.innerHTML = `<i class="fas fa-table"></i> syntasa-saas.ccdp_demo.web_tb_event`;

    // Column list
    const ul = document.createElement("ul");
    data.columns_used.forEach(col => {
        const li = document.createElement("li");
        li.textContent = col;
        ul.appendChild(li);
    });

    // Append everything
    inner.appendChild(h4);
    inner.appendChild(ul);
    card.appendChild(inner);
    container.appendChild(card);
}


function updateSQLBox(data) {
    const sqlOutput = document.getElementById("sql_code_output");    
    sqlOutput.textContent = data.filter_clause || ""; 
}
function updateDataBox(data) {
    console.log('data in updateDataBox:', data.matching_users);
    const dataParagraph = document.querySelector("#audience-data .data-content p");

    if (data.matching_users == 'null') {
        dataParagraph.textContent = "❌Failed to retrieve the number of users in the audience.";
    } else {
        dataParagraph.textContent = `The number of users in the audience is ${data.matching_users}.`;
    }
}


function toggleInfo() {
    const card = document.getElementById("info-card");
    card.classList.toggle("hidden");
}

function resetDataSources() {
    const container = document.querySelector(".data-sources-grid");
    container.innerHTML = `
        <div class="data-card used">
            <div class="card-inner hidden">
                <h4><i class="fas fa-table"></i><span class="badge"></span></h4>
                <ul>
                    <li></li>
                </ul>
            </div>
        </div>
        <div class="data-card used">
            <div class="card-inner hidden">
                <h4><i class="fas fa-table"></i><span class="badge"></span></h4>
                <ul>
                    <li></li>
                </ul>
            </div>
        </div>
        <div class="data-card used">
            <div class="card-inner hidden">
                <h4><i class="fas fa-table"></i><span class="badge"></span></h4>
                <ul>
                    <li></li>
                </ul>
            </div>
        </div>
        <div class="data-card">
            <div class="card-inner hidden">
                <h4><i class="fas fa-table"></i></h4>
                <ul>
                    <li></li>
                </ul>
            </div>
        </div>
    `;
}

document.addEventListener("DOMContentLoaded", () => {
    setupAudienceFeedbackButtons();
});

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function setupAudienceFeedbackButtons() {
    const feedbackContainer = document.querySelector(".query-feedback-buttons");
    if (!feedbackContainer) return;

    feedbackContainer.addEventListener("click", async function (e) {
        if (e.target.closest(".btn.helpful")) {
            console.log("Audience Helpful clicked");
            await sendFeedback("thumbs_up");
        }
        if (e.target.closest(".btn.not-helpful")) {
            console.log("Audience Not Helpful clicked");
            await sendFeedback("thumbs_down");
        }
    });
}

async function sendFeedback(feedbackType, event) {
    console.log("Sending feedback");
    const feedbackInput = document.getElementById('feedback-input');
    const feedbackText = feedbackInput ? feedbackInput.value : "";
    const question = document.getElementById("question").value;

    let csrfToken = null;
    const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfInput) {
        csrfToken = csrfInput.value;
    } else {
        csrfToken = getCookie("csrftoken");
    }

    let feedbackMsg = document.getElementById("feedback-message");

    // Show the message immediately after clicking the button
    feedbackMsg.textContent = "Thanks for providing your feedback!";

    try {
        const response = await fetch("/submit_feedback/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken,
            },
            body: JSON.stringify({
                feedback: feedbackType,          
                feedback_text: feedbackText,    
                attribute_goal: attributeGoal,  
                filter_clause: filterClause,     
                columns_used: columnsUsed,  
            }),
        });

        const result = await response.json();
        console.log(result.message || result.error);

        // Clear the input box after submitting
        if (feedbackInput) feedbackInput.value = '';

    } catch (error) {
        console.error(`Error submitting ${feedbackType} feedback:`, error);
    }
}
