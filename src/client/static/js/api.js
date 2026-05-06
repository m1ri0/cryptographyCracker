function createHashElement(hashData) {
    let value = hashData.password ? hashData.password : hashData.hash;

    return `
        <div class="endpoint-wrapper" style="margin-bottom: 10px;">
            <div class="endpoint-container" data-id="${hashData.id}">
                <span class="${hashData.status}">
                    ${hashData.status}
                </span>
                <span class="hash">
                    ${value}
                </span>
            </div>

            <div class="hash-details" id="details-${hashData.id}" style="display: none;">
                <em>Buscando detalhes...</em>
            </div>
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
        const hashId = $(this).data('id');
        const detailsDiv = $(`#details-${hashId}`);

        detailsDiv.slideToggle('fast');

        if(detailsDiv.data('loaded')) return;

        try {
            const response = await fetch(`/cripto_crack/hash/${hashId}`);
            if (!response.ok) throw new Error("Erro ao buscar detalhes");

            const data = await response.json();

            detailsDiv.html(`<pre>${JSON.stringify(data, null, 2)}</pre>`);
            
            detailsDiv.data('loaded', true);
        }
        catch (error) {
            console.error("Error fetching hash details:", error);
        }
    });
});