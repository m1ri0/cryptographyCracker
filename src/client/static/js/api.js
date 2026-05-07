function createHashElement(hashData) {
    let value = hashData.password ? hashData.password : hashData.hash;

    return `
        <div class="endpoint-wrapper" style="margin-bottom: 10px;">
            <div class="endpoint-container endpoint-${hashData.status}" data-id="${hashData.id}">
                <span class="${hashData.status}">
                    ${hashData.status}
                </span>
                <span class="hash">
                    ${value}
                </span>
            </div>

            <div class="hash-details hash-details-${hashData.status}" id="details-${hashData.id}" style="display: none;">
            </div>
        </div>
    `;
}

function createHashDetailsElement(detailsData) {
    return `
        <div class="details-content">
            <div class="detail-row detail-row-${detailsData.status}">
                <strong>ID:</strong> <span>${detailsData.id}</span>
            </div>
            <div class="detail-row detail-row-${detailsData.status}">
                <strong>Hash Original:</strong> <span class="hash-text">${detailsData.hash}</span>
            </div>
            <div class="detail-row detail-row-${detailsData.status}">
                <strong>Status:</strong> <span class="status-badge ${detailsData.status}">${detailsData.status}</span>
            </div>
            ${detailsData.password ? `
            <div class="detail-row detail-row-${detailsData.status} highlight">
                <strong>Senha Descoberta:</strong> <span class="pass-text">${detailsData.password}</span>
            </div>` : ''}
        </div>
    `;
}

function createHashListContainer(data) {
    const container = document.getElementById('hashes-list-container');
    container.innerHTML = '';

    data.hashes.forEach(item => {
        container.innerHTML += createHashElement(item);
    });
}

async function fetchAllHashes() {
    try {
        const response = await fetch('/cripto_crack/all-hashes');

        if (!response.ok) throw new Error("Error on the request");

        const data = await response.json();

        console.log("Data received from the server:", data);
        return data;
    }
    catch (error) {
        console.error("Error fetching hashes:", error);
        return null;
    }
};

$(document).ready(async function() {
    const result = await fetchAllHashes();
    createHashListContainer(result);

    $('#hashes-list-container').on('click', '.endpoint-container', async function() {
        $(this).toggleClass('active');
        const hashId = $(this).data('id');
        const detailsDiv = $(`#details-${hashId}`);

        detailsDiv.slideToggle('fast');

        if(detailsDiv.data('loaded')) return;

        try {
            const response = await fetch(`/cripto_crack/hash/${hashId}`);
            if (!response.ok) throw new Error("Erro ao buscar detalhes");

            const data = await response.json();

            detailsDiv.html(createHashDetailsElement(data));
            
            detailsDiv.data('loaded', true);
        }
        catch (error) {
            console.error("Error fetching hash details:", error);
        }
    });
});