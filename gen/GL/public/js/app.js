import * as THREE from 'three'
import {OrbitControls} from 'https://cdn.jsdelivr.net/npm/three@0.160.1/examples/jsm/controls/OrbitControls.js';
import {GLTFLoader} from 'https://cdn.jsdelivr.net/npm/three@0.160.1/examples/jsm/loaders/GLTFLoader.js';
import {EXRLoader} from 'https://cdn.jsdelivr.net/npm/three@0.160.1/examples/jsm/loaders/EXRLoader.js';
import {PMREMGenerator} from 'https://cdn.jsdelivr.net/npm/three@0.160.1/src/extras/PMREMGenerator.js';


// Initialize Three.js
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({antialias: true, alpha: true});

// camera position in one line:
camera.position.set(0, 0, 3);
//camera look at in one line:
camera.lookAt(-1, 3, 0);
// Add camera controls
const controls = new OrbitControls(camera, renderer.domElement);

renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);


// clear color as light gray
renderer.setClearColor(0xdddddd);

// Add event listeners for buttons
document.getElementById('btnCanvas').addEventListener('click', () => toggleModel('canvas'));
document.getElementById('btnPoster').addEventListener('click', () => toggleModel('poster'));
document.getElementById('btnHoodie').addEventListener('click', () => toggleModel('hoodie'));


// Load 3 models: canvas, poster, and hoodie
const modelPaths = {
	'canvas': 'assets/canvas/canvas.gltf',
	'poster': 'assets/poster/poster.gltf',
	'hoodie': 'assets/hoodie/chest.gltf'
};
const models = {};

let canvasMaterial, posterMaterial, hoodieMaterial;
let pendingTexture = null;

//current path
const loader = new GLTFLoader().setPath('./');

function loadModel(modelName, path) {
    loader.load(path, function (gltf) {
        models[modelName] = gltf.scene;
        models[modelName].visible = modelName === 'canvas'; // make canvas visible by default
        scene.add(gltf.scene);
		gltf.scene.rotation.set(0, -Math.PI / 2, 0);
        gltf.scene.traverse(function (child) {
            if (child.isMesh) {
                let material;
                if (child.name === "Plane") {
                    material = canvasMaterial = child.material;
					gltf.scene.position.set(0, 0, -1);
                } else if (child.name === "poster_mesh") {
                    material = posterMaterial = child.material;
					gltf.scene.position.set(0, 0, -2);
                } else if (child.name === "chest") {
                    material = hoodieMaterial = child.material;
					gltf.scene.position.set(0, 0, -1);
					gltf.scene.scale.set(1.3, 1.3, 1.3);
                }

                if (material && pendingTexture) {
                    material.map = pendingTexture;
                    material.needsUpdate = true;
                }
            }
        });
    }, undefined, function (error) {
        console.error(`Error loading model ${modelName}:`, error);
    });
}

function changeTextureFromUrl(imageUrl) {
    console.log("Loading texture from URL:", imageUrl);
    const textureLoader = new THREE.TextureLoader();
    textureLoader.load(imageUrl, function (texture) {
        console.log("Texture loaded", texture);
        texture.center.set(0.5, 0.5); // Set the center of rotation to the center of the texture
        texture.rotation = Math.PI; // Rotate the texture by 180 degrees

        pendingTexture = texture; // Set the pending texture

        // Update materials if they exist
        [canvasMaterial, posterMaterial, hoodieMaterial].forEach(material => {
            if (material) {
                material.map = texture;
                material.needsUpdate = true;
            }
        });
    });
}


// Function to change the texture of the model from file
function changeTextureFromFile(imageFile) {
	console.log("changeTexture called with:", imageFile.name);
	changeTextureFromUrl(URL.createObjectURL(imageFile))
}


const textureLoader = new THREE.TextureLoader();
textureLoader.load('assets/background/forest.png', function (texture) {
    const envMap = texture;

    // Assuming the PNG is an equirectangular panorama, set the mapping accordingly
    envMap.mapping = THREE.EquirectangularReflectionMapping;
    envMap.encoding = THREE.NoColorSpace;

    // Apply it as a background if needed
    scene.background = envMap;

    // Also set it as the environment for materials if you're using PBR materials
    scene.environment = envMap;

    // Update lighting if needed
    updateLighting();
});


// Function to update lighting to use the environment map for reflections and illumination
function updateLighting() {
	scene.traverse((obj) => {
		if (obj.isMesh && obj.material) {
			obj.material.envMap = scene.environment;
			obj.material.needsUpdate = true;
		}
	});
}

// Add event listener to the file input
document.getElementById('fileInput').addEventListener('change', function (event) {
	if (event.target.files.length > 0) {
		changeTextureFromFile(event.target.files[0]);
	}
});

window.toggleModel = changeVisibleModel;

// Function to change the visible model
function changeVisibleModel(visibleModelName) {
	for (let name in models) {
		if (models[name]) models[name].visible = (name === visibleModelName);
	}
}


// Render loop
let then = performance.now();
function animate() {
    requestAnimationFrame(animate);
    
    const now = performance.now();
    const elapsed = now - then;

    if (elapsed > (1000 / 24)) { // Throttle to 24fps
        controls.update();
        renderer.render(scene, camera);
        then = now;
    }
}

function init(){
	for (let name in modelPaths) {
		loadModel(name, modelPaths[name]);
	}
	if (initialTextureUrl) {
        changeTextureFromUrl(initialTextureUrl);
    }
}
document.getElementById('background-selector').addEventListener('change', function(event) {
    const selectedBackground = event.target.value;
    setBackground(selectedBackground);
});

function setBackground(imageFileName) {
    const textureLoader = new THREE.TextureLoader();
    textureLoader.load('assets/background/' + imageFileName, function (texture) {
        texture.mapping = THREE.EquirectangularReflectionMapping;
        texture.encoding = THREE.sRGBEncoding;

        // Update the background
        scene.background = texture;

        // Regenerate the environment map for PBR materials
        const pmremGenerator = new PMREMGenerator(renderer);
        pmremGenerator.compileEquirectangularShader();

        const rt = pmremGenerator.fromEquirectangular(texture);
        pmremGenerator.dispose();

        // Set the new texture as the environment map for the scene and all materials
        scene.environment = rt.texture;

        // Update the reflectance of all PBR materials in the scene
        scene.traverse((obj) => {
            if (obj.isMesh && obj.material && obj.material.isMeshStandardMaterial) {
                obj.material.envMap = rt.texture;
                obj.material.needsUpdate = true;
            }
        });

        // If your materials are not of the standard type, ensure you set their envMap property accordingly.
        // Update materials if they exist
        [canvasMaterial, posterMaterial, hoodieMaterial].forEach(material => {
            if (material && material.isMeshStandardMaterial) { // Check if it's a PBR material
                material.envMap = rt.texture;
                material.needsUpdate = true;
            }
        });

        // Rerender the scene with the new environment
        renderer.render(scene, camera);
    });
}


init();
animate();
