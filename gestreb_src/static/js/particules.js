particlesJS("particles-js", {
     "particles": {
         "number": {
             "value": 80,
             "density": {
                 "enable": true,
                 "value_area": 400
             }
         },
         "color": {
             "value": "#043c14"
         },
         "shape": {
             "type": "circle",
             "stroke": {
                 "width": 0,
                 "color": "#000000"
             },
             "polygon": {
                 "nb_sides": 4
             },
             "image": {
                 "src": "img/github.svg",
                 "width": 100,
                 "height": 100
             }
         },
         "opacity": {
             "value": 0.5,
             "random": false,
             "anim": {
                 "enable": false,
                 "speed": 1,
                 "opacity_min": 0.1,
                 "sync": false
             }
         },
         "size": {
             "value": 3,
             "random": true,
             "anim": {
                 "enable": false,
                 "speed": 50,
                 "size_min": 0.1,
                 "sync": false
             }
         },
         "line_linked": {
             "enable": true,
             "distance": 300,
             "color": "#042a19",
             "opacity": 0.7,
             "width": 1
         },
         "move": {
             "enable": true,
             "speed": 8,
             "direction": "none",
             "random": false,
             "straight": false,
             "out_mode": "out",
             "bounce": false,
             "attract": {
                 "enable": false,
                 "rotateX": 600,
                 "rotateY": 1200
             }
         }
     },
     "interactivity": {
         "detect_on": "canvas",
         "events": {
             "onhover": {
                 "enable": true,
                 "mode": "repulse"
             },
             "onclick": {
                 "enable": true,
                 "mode": "push"
             },
             "resize": true
         },
         "modes": {
             "grab": {
                 "distance": 200,
                 "line_linked": {
                     "opacity": 1
                 }
             },
             "bubble": {
                 "distance": 400,
                 "size": 30,
                 "duration": 1,
                 "opacity": 8,
                 "speed": 3
             },
             "repulse": {
                 "distance": 200,
                 "duration": 0.4
             },
             "push": {
                 "particles_nb": 10
             },
             "remove": {
                 "particles_nb": 2
             }
         }
     },
     "retina_detect": true
 });
 