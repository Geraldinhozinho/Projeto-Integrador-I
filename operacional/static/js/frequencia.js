let html5QrCode;
let isScanning = false;
let tipoRegistroAtual = 'entrada';

function abrirModalRegistro() {
    const btn = document.getElementById('btn-registrar-frequencia');
    
    if (!btn) {
        console.error('ERRO CRÍTICO: Botão #btn-registrar-frequencia não existe no HTML!');
        alert('Erro interno: Botão de registro não encontrado.');
        return;
    }
    
    const statusAtual = btn.dataset.statusAtual; 
    
    console.log('DEBUG JS - Status lido do HTML:', statusAtual);
    console.log('DEBUG JS - Texto visível do botão:', btn.innerText.trim());

    if (statusAtual === 'EM_ABERTO') {
        tipoRegistroAtual = 'saida';
    } else {
        tipoRegistroAtual = 'entrada';
    }
    
    console.log('Tipo de registro definido pelo JS:', tipoRegistroAtual);
    
    abrirModalConfirmacao(tipoRegistroAtual);
}

function abrirModalConfirmacao(tipo) {
    tipoRegistroAtual = tipo;
    const agora = new Date();
    
    const dataFormatada = agora.toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
    
    const horaFormatada = agora.toLocaleTimeString('pt-BR', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    
    const dataEl = document.getElementById('data-registro');
    const horaEl = document.getElementById('hora-registro');
    const tipoEl = document.getElementById('tipo-registro');
    
    if (dataEl) dataEl.textContent = dataFormatada;
    if (horaEl) horaEl.textContent = horaFormatada;
    if (tipoEl) tipoEl.textContent = tipo === 'entrada' ? 'Entrada' : 'Saída';
    
    const modal = document.getElementById('modal-confirmacao');
    if (modal) {
        modal.style.display = 'flex';
    }
}

function fecharModalConfirmacao() {
    const modal = document.getElementById('modal-confirmacao');
    if (modal) {
        modal.style.display = 'none';
    }
}

function confirmarRegistro() {
    fecharModalConfirmacao();
    
    const modalConcluido = document.getElementById('modal-concluido');
    if (modalConcluido) {
        modalConcluido.style.display = 'flex';
    }
    
    const form = document.createElement('form');
    form.method = 'post';
    form.style.display = 'none';
    
    const btn = document.getElementById('btn-registrar-frequencia');
    if (!btn) {
        alert('Erro: Botão não encontrado');
        return;
    }
    
    if (tipoRegistroAtual === 'entrada') {
        form.action = btn.dataset.urlEntrada;
    } else {
        form.action = btn.dataset.urlSaida;
    }
    
    console.log('Enviando para:', form.action, 'Tipo:', tipoRegistroAtual);
    
    const csrfElement = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfElement) {
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = csrfElement.value;
        form.appendChild(csrfInput);
    }
    
    const bolsistaInput = document.createElement('input');
    bolsistaInput.type = 'hidden';
    bolsistaInput.name = 'bolsista_id';
    bolsistaInput.value = '1'; 
    form.appendChild(bolsistaInput);
    
    document.body.appendChild(form);
    form.submit();
    
    setTimeout(function() {
        window.location.href = window.location.href + '?t=' + new Date().getTime();
    }, 1500);
}

function abrirScanner() {
    const modal = document.getElementById('scanner-modal');
    if (modal) {
        modal.style.display = 'flex';
    }
    iniciarCamera();
}

function fecharScanner() {
    const modal = document.getElementById('scanner-modal');
    if (modal) {
        modal.style.display = 'none';
    }
    
    if (html5QrCode) {
        html5QrCode.stop().catch(function(err) {
            console.log(err);
        });
    }
    
    const feedback = document.getElementById('scanner-feedback');
    const matriculaInput = document.getElementById('matricula-input');
    
    if (feedback) feedback.innerText = '';
    if (matriculaInput) matriculaInput.value = '';
    
    isScanning = false;
}

function iniciarCamera() {
    if (isScanning) return;
    isScanning = true;
    
    html5QrCode = new Html5Qrcode('reader');
    
    html5QrCode.start(
        { facingMode: 'environment' }, 
        { fps: 10, qrbox: { width: 250, height: 250 } },
        onScanSuccess,
        function() {} 
    ).catch(function(err) {
        const feedback = document.getElementById('scanner-feedback');
        if (feedback) {
            feedback.innerText = 'Erro ao acessar câmera. Verifique as permissões.';
            feedback.style.color = 'red';
        }
        isScanning = false;
    });
}

async function onScanSuccess(decodedText) {
    if (!isScanning) return;
    isScanning = false;
    
    const matriculaInput = document.getElementById('matricula-input');
    const feedback = document.getElementById('scanner-feedback');
    
    const matricula = matriculaInput ? matriculaInput.value.trim() : '';
    
    if (!matricula) {
        if (feedback) {
            feedback.innerText = 'Por favor, digite sua matrícula primeiro.';
            feedback.style.color = 'red';
        }
        isScanning = true;
        return;
    }

    if (feedback) {
        feedback.innerText = 'Processando...';
        feedback.style.color = 'blue';
    }

    try {
        const btnQr = document.querySelector('.btn-escanear-qr');
        const apiUrl = btnQr ? btnQr.dataset.apiUrl : '/frequencia/registrar-qr/';

        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({ token: decodedText, matricula: matricula })
        });

        const data = await response.json();

        if (data.sucesso) {
            if (feedback) {
                feedback.innerText = 'Sucesso: ' + data.mensagem;
                feedback.style.color = 'green';
            }
            html5QrCode.stop();
            setTimeout(function() {
                window.location.href = window.location.href + '?t=' + new Date().getTime();
            }, 1500);
        } else {
            if (feedback) {
                feedback.innerText = 'Erro: ' + data.mensagem;
                feedback.style.color = 'red';
            }
            isScanning = true; 
        }
    } catch (error) {
        if (feedback) {
            feedback.innerText = 'Erro de conexão com o servidor.';
            feedback.style.color = 'red';
        }
        isScanning = true;
    }
}