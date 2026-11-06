document.addEventListener('DOMContentLoaded', function() {
            const modal = document.getElementById('modalIndeferir');
            const btnIndeferir = document.getElementById('btnIndeferir');
            const btnCancelar = document.getElementById('btnCancelar');
            const motivoRejeicao = document.getElementById('motivoRejeicao');
            
            btnIndeferir.addEventListener('click', function() {
                modal.style.display = 'flex';
            });
            
            btnCancelar.addEventListener('click', function() {
                modal.style.display = 'none';
                motivoRejeicao.value = '';
            });
            
            modal.addEventListener('click', function(e) {
                if (e.target === modal) {
                    modal.style.display = 'none';
                    motivoRejeicao.value = '';
                }
            });
            
            document.addEventListener('keydown', function(e) {
                if (e.key === 'Escape' && modal.style.display === 'flex') {
                    modal.style.display = 'none';
                    motivoRejeicao.value = '';
                }
            });
        });