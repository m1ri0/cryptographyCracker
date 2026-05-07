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
    const btnCrack = detailsData.status === 'pending'
        ? `<button class="btn-crack" data-id="${detailsData.id}">Crack</button>`
        : '';

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
            <div class="detail-actions">
                ${btnCrack}
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

function closeModal() {
    const modal = $('#modal-overlay');

    modal.addClass('hide');

    setTimeout(() => {
        modal.remove();
    }, 300);
}

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

    $('#hashes-list-container').on('click', '.btn-crack', async function(event) {
        event.stopPropagation();

        const HashId = $(this).data('id');

        try {
            const response = await fetch(`/cripto_crack/crack/${HashId}`, { method: 'POST' });
            if (!response.ok) throw new Error("Erro ao iniciar o processo de cracking");

            const data = await response.json();
            console.log("Crack process started:", data);
        }
        catch (error) {
            console.error("Error starting crack process:", error);
        }
    });

    $('#add-pass-btn').on('click', function() {
        const modalHtml = `
            <div id="modal-overlay" class="modal-overlay">
                <div class="modal-content">
                    <h3>Inserir senha para gerar hash</h3>
                    <input type="password" id="password-input" placeholder="Digite a senha..." class="password-input">
                    <div class="modal-actions">
                        <button id="save-pass-btn" class="btn-action">Salvar</button>
                        <button id="close-modal-btn" class="btn-action">Cancelar</button>
                    </div>
                </div>
            </div>
        `;
        $('body').append(modalHtml);
    });

    $('body').on('click', '#close-modal-btn', function() {
        closeModal();
    });

    $('body').on('click', '#modal-overlay', function(event) {
        if (event.target === this) {
            closeModal();
        }
    });

    $('body').on('click', '#save-pass-btn', async function() {
        const password = $('#password-input').val().trim();
        if (!password) {
            alert("Por favor, insira uma senha válida.");
            return;
        }

        try {
            const response = await fetch(`/cripto_crack/add-password?password=${password}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ password })
            });

            if (!response.ok) throw new Error("Erro ao adicionar a senha");

            const data = await response.json();
            console.log("Senha adicionada com sucesso:", data);

            const allHashes = await fetchAllHashes();
            createHashListContainer(allHashes);
        }
        catch (error) {
            console.error("Error adding password:", error);
        }
        finally {
            $('#modal-overlay').remove();
        }
    });
});