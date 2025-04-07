
// import * as THREE from '/node_modules/three/build/three.module.js';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { FontLoader } from 'three/examples/jsm/loaders/FontLoader';
import { TextGeometry } from 'three/examples/jsm/geometries/TextGeometry';

import helvetica from 'three/examples/fonts/helvetiker_regular.typeface.json?url';

import { makeMap } from './geo.js';

/* threejs:
x: positiv is right
y: positiv is up
z: positiv is towards the viewer
*/

const useMap = true

const scene = new THREE.Scene();
scene.background = new THREE.Color(0xf0f0f0);


// Camera
const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.set(20, 20, 20);
camera.lookAt(0, 0, 0);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.target.set(0, 0, 0);
controls.update();


const light = new THREE.AmbientLight(0xffffff, 0.8)
scene.add(light);

const dirLight1 = new THREE.DirectionalLight(0xff0000, 3);
dirLight1.position.set(10, 100, 100);
scene.add(dirLight1);


const dirLight2 = new THREE.DirectionalLight(0x00ffff, 5);
dirLight2.position.set(50, 100, 75);
scene.add(dirLight2);

const gridHelper = new THREE.GridHelper(50, 50);
scene.add(gridHelper);


const axesHelper = new THREE.AxesHelper(10);
scene.add(axesHelper);
const createAxisLabel = (text, position) => {
  const canvas = document.createElement('canvas');
  const context = canvas.getContext('2d');
  context.font = '24px Arial';
  context.fillStyle = 'black';
  context.fillText(text, 0, 24);

  const texture = new THREE.CanvasTexture(canvas);
  const spriteMaterial = new THREE.SpriteMaterial({ map: texture });
  const sprite = new THREE.Sprite(spriteMaterial);
  sprite.scale.set(5, 2, 2);
  sprite.position.copy(position);
  return sprite;
};

scene.add(createAxisLabel('X', new THREE.Vector3(11, 0, 0)));
scene.add(createAxisLabel('Y', new THREE.Vector3(0, 11, 0)));
scene.add(createAxisLabel('Z', new THREE.Vector3(0, 0, 11)));

const pyramidGeometry = new THREE.ConeGeometry(1, 2, 4);
const pyramidMaterial = new THREE.MeshStandardMaterial({ color: 0xffa500 });
const pyramid = new THREE.Mesh(pyramidGeometry, pyramidMaterial);
pyramid.position.set(-10, 1, 1); // Adjust Y position to place the base at Y=0
scene.add(pyramid);


// add extuded shape
const shape = new THREE.Shape();
shape.moveTo(0, 0);
shape.lineTo(0, 1);
shape.lineTo(1, 1);
shape.lineTo(1, 0);
shape.closePath();
const extrudeSettings = { steps: 2, depth: 2, bevelEnabled: true, bevelThickness: 0, bevelSize: 0, bevelSegments: 1 };
const geometry = new THREE.ExtrudeGeometry(shape, extrudeSettings);
const material = new THREE.MeshStandardMaterial({ color: 0xffff00, side: THREE.DoubleSide }); // Top and bottom faces
const sideMaterial = new THREE.MeshStandardMaterial({ color: 0x008080, side: THREE.DoubleSide }); // Side faces
const mesh = new THREE.Mesh(geometry, [material, sideMaterial]);
mesh.position.set(5, 5, 0.5);
scene.add(mesh);


// font
const floader = new FontLoader();
const font = await floader.loadAsync(helvetica)
const txt = "blah 123"
const txtGeo = new TextGeometry(txt, {
  font,
  size: 1,
  depth: .1,
  curveSegments: 6,
  bevelEnabled: true,
  bevelThickness: 0,
  bevelSize: 0,
  bevelOffset: 0,
  bevelSegments: 1
});
const txtMaterial = new THREE.MeshBasicMaterial({ color: 0xff0000, side: THREE.DoubleSide });
const txtMesh = new THREE.Mesh(txtGeo, txtMaterial);
txtMesh.position.set(5, 6, 1);
scene.add(txtMesh);

// gltf
const gloader = new GLTFLoader();
const prg = (xhr) => { console.log((xhr.loaded / xhr.total * 100) + '% loaded') }

const gltf = await gloader.loadAsync('/preview.glb', prg)
const model = gltf.scene;
scene.add(model);

// Optional: center the model
const box = new THREE.Box3().setFromObject(model);
const center = new THREE.Vector3();
box.getCenter(center);
model.position.sub(center);

if (useMap) {
  const buildings = await makeMap()
  buildings.position.set(0, 0, 0);
  buildings.rotation.x = -Math.PI / 2; // Rotate 45 degrees around the X-axis
  scene.add(buildings);
}


/*
loader.load('preview.glb', function (gltf) {
  const model = gltf.scene;
  scene.add(model);

  // Optional: center the model
  const box = new THREE.Box3().setFromObject(model);
  const center = new THREE.Vector3();
  box.getCenter(center);
  model.position.sub(center);

  
  animate();
}, undefined, function (error) {
  console.error('Error loading preview.glb:', error);
});
*/

function animate() {
  requestAnimationFrame(animate);
  renderer.render(scene, camera);
}

animate();


window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

