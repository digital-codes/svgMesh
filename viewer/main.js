
  // import * as THREE from '/node_modules/three/build/three.module.js';
  import * as THREE from 'three';
  import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
  import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

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
  

  const loader = new GLTFLoader();
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

  function animate() {
    requestAnimationFrame(animate);
    renderer.render(scene, camera);
  }

  window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });

