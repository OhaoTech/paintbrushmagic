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

// Load the model

let hoodieMaterial;
let pendingTexture = null;

//current path
const loader = new GLTFLoader().setPath('./');
loader.load('chest.gltf', function (gltf) {
	let materialFound = false;
    gltf.scene.traverse(function (child) {
        if (child.isMesh && child.name === "chest") {
			materialFound = true;
			console.log(`Material found for mesh ${child.name}`, hoodieMaterial);

            // Save the material for later use
            hoodieMaterial = child.material;
			// console.log("Material found:", hoodieMaterial);
			if(pendingTexture){
				hoodieMaterial.map = pendingTexture;
				hoodieMaterial.needsUpdate = true;
				pendingTexture = null;
			}
			return;
        }
    });
	//move the model to the center
	gltf.scene.position.set(0, 0, 0);
	//rotate along Z axis 90 degrees clockwise
	gltf.scene.rotation.set(0,  - Math.PI / 2, 0);
    scene.add(gltf.scene);
	if(!materialFound){
		console.error("Material not found in the model");
	}
}, undefined, function (error) {
    console.error(error);
});

// Function to change the texture of the hoodie
function changeTexture(imageFile) {
    console.log("changeTexture called with:", imageFile.name);
    const textureLoader = new THREE.TextureLoader();
    textureLoader.load(URL.createObjectURL(imageFile), function (texture) {
        console.log("Texture loaded", texture);
        // Rotate the texture by 180 degrees
		texture.center.set(0.5, 0.5); // Set the center of rotation to the center of the texture
		texture.rotation = Math.PI; // Rotate the texture by 180 degrees (Math.PI radians)
	
        if (hoodieMaterial) {
            console.log("Previous material map:", hoodieMaterial.map);
            hoodieMaterial.map = texture;
            hoodieMaterial.needsUpdate = true;
            console.log("New material map:", hoodieMaterial.map);
        } else {
            console.error("Hoodie material not found.");
            pendingTexture = texture;
        }
    });
}


const pmremGenerator = new PMREMGenerator(renderer);
pmremGenerator.compileEquirectangularShader();
const exrLoader = new EXRLoader();
exrLoader.setDataType(THREE.HalfFloatType);
exrLoader.load('4k.exr', function (texture) {
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



// Render loop
function animate() {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
}

animate();
