import * as THREE from 'three'
import { OrbitControls } from 'https://cdn.jsdelivr.net/npm/three@0.160.1/examples/jsm/controls/OrbitControls.js';
import { GLTFLoader } from 'https://cdn.jsdelivr.net/npm/three@0.160.1/examples/jsm/loaders/GLTFLoader.js';
import { EXRLoader } from 'https://cdn.jsdelivr.net/npm/three@0.160.1/examples/jsm/loaders/EXRLoader.js';
import { PMREMGenerator } from 'https://cdn.jsdelivr.net/npm/three@0.160.1/src/extras/PMREMGenerator.js';



// Initialize Three.js
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });

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
	loader.load(path, function(gltf) {
		models[modelName] = gltf.scene;
		models[modelName].visible = false;
		scene.add(gltf.scene);

		if(modelName === 'canvas'){
			models['canvas'].visible = true;
			gltf.scene.position.set(0, 0, -1);
		}
		if(modelName === 'poster'){
			gltf.scene.position.set(0, 0, -2);
		}
		if(modelName === 'hoodie'){//scale up
			gltf.scene.position.set(0, 0, -1);
			gltf.scene.scale.set(1.3, 1.3, 1.3);
		}
		
		gltf.scene.rotation.set(0,  - Math.PI / 2, 0);
		gltf.scene.traverse(function(child) {
			//mesh name is "Plane", "Chest" or "poster_mesh" simultaneously
			if(child.isMesh && child.name === "Plane"){
				canvasMaterial = child.material;
				if(pendingTexture){
					canvasMaterial.map = pendingTexture;
					canvasMaterial.needsUpdate = true;
					pendingTexture = null;
				}
			}

			if(child.isMesh && child.name === "poster_mesh"){
				posterMaterial = child.material;
				if(pendingTexture){
					posterMaterial.map = pendingTexture;
					posterMaterial.needsUpdate = true;
					pendingTexture = null;
				}
			}

			if(child.isMesh && child.name === "chest"){
				hoodieMaterial = child.material;
				if(pendingTexture){
					hoodieMaterial.map = pendingTexture;
					hoodieMaterial.needsUpdate = true;
					pendingTexture = null;
				}
			}
			
		}, undefined, function(error) {
			console.error("Error loading model ${modelName}", error);
		});
	});
}

for (let name in modelPaths) {
	loadModel(name, modelPaths[name]);
}


// Function to change the texture of the hoodie
function changeTexture(imageFile) {
    console.log("changeTexture called with:", imageFile.name);
    const textureLoader = new THREE.TextureLoader();
    textureLoader.load(URL.createObjectURL(imageFile), function (texture) {
        console.log("Texture loaded", texture);
        // Rotate the texture by 180 degrees
		texture.center.set(0.5, 0.5); // Set the center of rotation to the center of the texture
		texture.rotation = Math.PI; // Rotate the texture by 180 degrees (Math.PI radians)
	

		if(canvasMaterial){
			canvasMaterial.map = texture;
			canvasMaterial.needsUpdate = true;
		}else{
			pendingTexture = texture;
		}

		if(posterMaterial){
			posterMaterial.map = texture;
			posterMaterial.needsUpdate = true;
		}else{
			pendingTexture = texture;
		}

		if(hoodieMaterial){
			hoodieMaterial.map = texture;
			hoodieMaterial.needsUpdate = true;
		}else{
			pendingTexture = texture;
		}

    });
}


const pmremGenerator = new PMREMGenerator(renderer);
pmremGenerator.compileEquirectangularShader();
const exrLoader = new EXRLoader();
exrLoader.setDataType(THREE.HalfFloatType);
exrLoader.load('assets/4k.exr', function (texture) {
	const envMap = pmremGenerator.fromEquirectangular(texture).texture;
	pmremGenerator.dispose();

	texture.encoding = THREE.LinearSRGBColorSpace;
	texture.mapping = THREE.EquirectangularReflectionMapping;
	scene.environment = envMap;
	scene.background = envMap;
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
        changeTexture(event.target.files[0]);
    }
});

window.toggleModel = changeVisibleModel;

// Function to change the visible model
function changeVisibleModel(visibleModelName) {
	for (let name in models) {
		if (models[name]) models[name].visible = (name === visibleModelName);
	}
	renderer.render(scene, camera);
}


// Render loop
function animate() {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
}


animate();
