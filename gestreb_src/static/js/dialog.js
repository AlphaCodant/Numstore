document.addEventListener('DOMContentLoaded', () => {
    const icons = document.querySelectorAll('.open-dialog');
    const dialogBox = document.getElementById('dialog-box');
    const cancelBtn = document.getElementById('cancel-btn');
    const saveBtn = document.getElementById('save-btn');
  
    icons.forEach(icon => {
      icon.addEventListener('click', (event) => {
        const iconPosition = icon.getBoundingClientRect();
        const dialogWidth = dialogBox.offsetWidth;
        
        // Positionner la boîte de dialogue près de l'icône
        dialogBox.style.left = `${iconPosition.left + iconPosition.width / 2 - dialogWidth / 2}px`;
        dialogBox.style.top = `${iconPosition.top + iconPosition.height}px`;
  
        // Afficher la boîte de dialogue
        dialogBox.style.display = 'block';
      });
    });
  
    // Bouton "Annuler" - fermer la boîte de dialogue
    cancelBtn.addEventListener('click', () => {
      dialogBox.style.display = 'none';
    });
  
    // Bouton "Enregistrer" - effectuer une action (par exemple, enregistrer une valeur)
    saveBtn.addEventListener('click', () => {
      alert('Valeur enregistrée !');
      dialogBox.style.display = 'none'; // Cacher la boîte de dialogue après l'action
    });
  });
  