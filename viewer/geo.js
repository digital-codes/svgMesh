
/* threejs:
x: positiv is right
y: positiv is up
z: positiv is towards the viewer
*/
import * as THREE from 'three';

const makeMap = async () => {

  const mapCenter = [935570.0651499415, 6276230.15514086]; // x,y Karlsruhe crs 3587
  const lonLatCenter = [8.4043688, 49.0080662]


  // load buildings
  const buildings = await fetch('/geo/Gebaeudeflaeche_merged.geojson').then(response => response.json());
  //console.log(buildings.features.slice(0,10));
  //scene.add(buildingsGroup);
  const makeBuildings = (buildings) => {
    const group = new THREE.Group();
    buildings.features.forEach(building => {
      const scale = 10
      const height = building.properties.hoehe / scale;
      const geom = building.geometry;
      let mpoly
      if (geom.type == 'Polygon') {
        mpoly = [geom.coordinates]
      } else if (geom.type == 'MultiPolygon') {
        mpoly = geom.coordinates
      } else console.error('unknown geometry type', geom.type)
      console.log(mpoly.length, mpoly[0].length, mpoly[0][0].length, mpoly[0][0][0].length)

      mpoly[0].forEach(polygon => {
        console.log(polygon)
        const shape = new THREE.Shape();
        polygon.forEach((point, index) => {
          point = [(point[0] - mapCenter[0]) / scale, (point[1] - mapCenter[1]) / scale];
          console.log(point)
          if (index === 0) {
            shape.moveTo(point[0], point[1]);
          } else {
            shape.lineTo(point[0], point[1]);
          }
        });
        shape.closePath();
        const extrudeSettings = { depth: height, bevelEnabled: true, bevelThickness: 0, bevelSize: 0, bevelSegments: 1  };
        const geometry = new THREE.ExtrudeGeometry(shape, extrudeSettings);
        const material = new THREE.MeshStandardMaterial({ color: 0x00ff00,side:THREE.DoubleSide }); // Top and bottom faces
        const sideMaterial = new THREE.MeshStandardMaterial({ color: 0x008080, side:THREE.DoubleSide }); // Side faces
        const mesh = new THREE.Mesh(geometry, [material, sideMaterial]);

        // Adjust position to account for extrusion along Z-axis
        console.log(mesh)
        //mesh.position.set(5, 5, height / 2);
        group.add(mesh);
      });

      /*
      const geometry = new THREE.BoxGeometry(1, 1, height);
      const material = new THREE.MeshStandardMaterial({ color: 0x00ff00 });
      const mesh = new THREE.Mesh(geometry, material);
      mesh.position.set(building.geometry.coordinates[0], building.geometry.coordinates[1], height / 2);
      group.add(mesh);
      */
    });
    return group;
  }
  const buildingsGroup = makeBuildings(buildings);
  return buildingsGroup

}

export { makeMap }

