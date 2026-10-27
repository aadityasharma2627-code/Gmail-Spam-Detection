document.addEventListener('DOMContentLoaded',()=>{
const ctx=document.getElementById('pieChart');
if(ctx){
new Chart(ctx,{
type:'pie',
data:{
labels:['Spam','Ham'],
datasets:[{data:[spam,ham],backgroundColor:['#dc3545','#198754']}]
},
options:{responsive:true}
});
}

const search=document.getElementById('searchBox');
if(search){
search.addEventListener('keyup',()=>{
const q=search.value.toLowerCase();
document.querySelectorAll('.email-card').forEach(c=>{
const s=c.querySelector('.email-subject').innerText.toLowerCase();
c.style.display=s.includes(q)?'':'none';
});
});
}

const dark=document.getElementById('darkToggle');
dark?.addEventListener('click',()=>{
document.body.classList.toggle('bg-dark');
document.body.classList.toggle('text-light');
document.querySelectorAll('.card').forEach(c=>c.classList.toggle('bg-dark'));
});

document.getElementById('scanForm')?.addEventListener('submit',()=>{
const b=document.getElementById('scanBtn');
b.disabled=true;
b.innerHTML='Scanning...';
});
});
