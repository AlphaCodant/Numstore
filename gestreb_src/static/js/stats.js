function stats(){
    document.getElementById('stats_stats').style.display='inline-block';
    $(document).ready(()=>{
        let donnees_stats = [];
        $.ajax({
            url:'/elements/elem',
            success: (data)=>{
                //donnees_stats.push(data.features.properties);
                console.log(data);
                let sup = 0;
                let superf = 0;
                let data_operateur = [];
                let sup_operateur =[];           
                for(let i=0;i<data.features.length;i++){
                    sup+=data.features[i].properties['superficie'];
                    superf = data.features[i].properties['superficie']
                    donnees_stats.push(superf)
                    
                    if (data.features[i].properties['partenaire'] in data_operateur){
                                console.log("ok");
                        }
                        else{
                            data_operateur.push(data.features[i].properties['partenaire']);
                        }
                    
                }
                

                console.log(data_operateur);
                document.getElementById("sup_totale").innerHTML=(Math.round(sup * 100)/100).toFixed(2)+ ' ha';
               //document.getElementById("sup_moyenne").innerHTML=(Math.round(sup/data.features.length * 100)/100).toFixed(2)+ ' ha';
                document.getElementById("sup_min").innerHTML=(Math.round(Math.min(...donnees_stats) * 100)/100).toFixed(2)+ ' ha';       
                document.getElementById("sup_max").innerHTML=(Math.round((Math.max(...donnees_stats)) * 100)/100).toFixed(2)+ ' ha';  
                document.getElementById("nb_parcelles").innerHTML=(Math.round(data.features.length * 100)/100);
                console.log(donnees_stats.sort())  
                function uniqueFilter(value, index, self) {
                    return self.indexOf(value) === index;
                }         
                let operateur = data_operateur.filter(uniqueFilter);
                console.log(operateur); 
                
                for(let j=0;j<operateur.length;j++){
                    let sup_op =0;
                    for(let k=0;k<data.features.length;k++){
                        if(data.features[k].properties['partenaire'] == operateur[j]){
                            sup_op+=data.features[k].properties['superficie'];
                        }
                    
                    }
                    sup_operateur.push(sup_op);
                }

                /*for (operateurs in operateur){
                    let ul = document.getElementById("nom_operateurs");
                    let li = document.createElement('li');
                    li.appendChild(document.createTextNode(`${operateur[operateurs]} ${(Math.round(sup_operateur[operateurs] * 100)/100).toFixed(2)} ha`));
                    ul.appendChild(li);
                }*/
                //document.getElementById("nom_operateurs").innerHTML=operateur[sup_operateur.indexOf(Math.max(...sup_operateur))];
                //document.getElementById("sup_operateurs").innerHTML=(Math.round(Math.max(...sup_operateur)* 100)/100).toFixed(2)+' ha';
                //document.getElementById("nb_operateur").innerHTML=(Math.round(operateur.length * 100)/100);
                

                console.log(sup_operateur);


            }
        })
})
};
