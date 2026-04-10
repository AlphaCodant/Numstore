var map, geojson, featureOverlay, overlays, style;
var selected, features, layer_name, layerControl;
var content;
var selectedFeature;
var declencheur=0;
let id;
let dn;

var view = new ol.View({
    projection: 'EPSG:4326',
    center: [-5.5294, 7.5610],
    zoom: 7.5,

});
var view_ov = new ol.View({
    projection: 'EPSG:4326',
    center: [-5.5294, 7.5610],
    zoom: 7.5,
});


var base_maps = new ol.layer.Group({
    'title': 'Cartes de fond',
    layers: [
        new ol.layer.Tile({
            title: 'Satellite',
            type: 'base',
            visible: true,
            source: new ol.source.XYZ({
                attributions: ['Powered by Esri',
                    'Source: Esri, DigitalGlobe, GeoEye, Earthstar Geographics, CNES/Airbus DS, USDA, USGS, AeroGRID, IGN, and the GIS User Community'
                ],
                attributionsCollapsible: false,
                url: 'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                maxZoom: 23
            })
        })
    ]
});

overlays = new ol.layer.Group({
    'title': 'Donnees',
    layers: [] 
});


var OSM = new ol.layer.Tile({
    source: new ol.source.OSM(),
    type: 'base',
    title: 'OSM',
});
let iterateur = [];

$(document).ready(()=>{
    style_contour_ci = new ol.style.Style({
        fill: new ol.style.Fill({
            color: 'rgba(236, 230, 217, 0.2)'
        }),
        
        stroke: new ol.style.Stroke({
            color: 'black',
            width: 0.5
        }),

        image: new ol.style.Circle({
            radius: 7,
            fill: new ol.style.Fill({
                color: 'cyan'
            })
        }),
        text: new ol.style.Text({
            font: 'bold 15px nunito',
            text:'CI',
            fill: new ol.style.Fill({
                color: 'black'
            })
        })
    });
    geojso = new ol.layer.Vector({
        title:`Contour CI`,
        //title: '<h5>' + value_crop+' '+ value_param +' '+ value_seas+' '+value_level+'</h5>',
        source: new ol.source.Vector({
            url: `/json/contour_ci.geojson`,
            format: new ol.format.GeoJSON()
        }),
        style: style_contour_ci
    });
    //console.log(forets_cl[i]);
    overlays.getLayers().push(geojso);
    style_contour_tene = new ol.style.Style({
        fill: new ol.style.Fill({
            color: 'rgba(236, 230, 217, 0.2)'
        }),
        
        stroke: new ol.style.Stroke({
            color: 'black',
            width: 0.5
        }),

        image: new ol.style.Circle({
            radius: 7,
            fill: new ol.style.Fill({
                color: 'cyan'
            })
        }),
        text: new ol.style.Text({
            font: 'bold 20px nunito',
            text:'Tene',
            fill: new ol.style.Fill({
                color: 'black'
            })
        })
    });
    geojson1 = new ol.layer.Vector({
        title:`Contour Foret classee Tene`,
        //title: '<h5>' + value_crop+' '+ value_param +' '+ value_seas+' '+value_level+'</h5>',
        source: new ol.source.Vector({
            url: `json/fc_gagnoa_tene.geojson`,
            format: new ol.format.GeoJSON()
        }),
        style: style_contour_tene
    });
    //console.log(forets_cl[i]);
    overlays.getLayers().push(geojson1);
    style_contour_sangoue = new ol.style.Style({
        fill: new ol.style.Fill({
            color: 'rgba(236, 230, 217, 0.2)'
        }),
        
        stroke: new ol.style.Stroke({
            color: 'black',
            width: 0.5
        }),

        image: new ol.style.Circle({
            radius: 7,
            fill: new ol.style.Fill({
                color: 'cyan'
            })
        }),
        text: new ol.style.Text({
            font: 'bold 20px nunito',
            text:'Sangoue',
            fill: new ol.style.Fill({
                color: 'black'
            })
        })
    });
    geojson2 = new ol.layer.Vector({
        title:`Contour Foret classee Sangoue`,
        //title: '<h5>' + value_crop+' '+ value_param +' '+ value_seas+' '+value_level+'</h5>',
        source: new ol.source.Vector({
            url: `json/fc_gagnoa_sangoue.geojson`,
            format: new ol.format.GeoJSON()
        }),
        style: style_contour_sangoue
    });
    //console.log(forets_cl[i]);
    overlays.getLayers().push(geojson2);
})

// Send a request




map = new ol.Map({
    target: 'map',
    view: view,
    // overlays: [overlay]
});


map.addLayer(base_maps);
map.addLayer(overlays);
//overlays.getLayers().push(cGGagnoa);
//overlays.getLayers().push(foretGagnoa);
var popup = new Popup();
map.addOverlay(popup);

var mouse_position = new ol.control.MousePosition();
map.addControl(mouse_position);
var slider = new ol.control.ZoomSlider();
map.addControl(slider);



var zoom_ex = new ol.control.ZoomToExtent({
    extent: [
        65.90, 7.48,
        98.96, 40.30
    ]
});
map.addControl(zoom_ex);

var scale_line = new ol.control.ScaleLine({
    units: 'metric',
    bar: true,
    steps: 6,
    text: true,
    minWidth: 140,
    target: 'scale_bar'
});
map.addControl(scale_line);

layerSwitcher = new ol.control.LayerSwitcher({
    activationMode: 'click',
    startActive: true,
    tipLabel: 'Layers', // Optional label for button
    groupSelectStyle: 'children', // Can be 'children' [default], 'group' or 'none'
    collapseTipLabel: 'Collapse layers',
});
map.addControl(layerSwitcher);

layerSwitcher.renderPanel();
