const json_headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

function alignCenter(strokes) {
    let maxX = 0;
    let maxY = 0;
    for (let stroke of strokes) {
        for (let point of stroke) {
            if (point[0] > maxX) {
                maxX = point[0];
            }
            if (point[1] > maxY) {
                maxY = point[1]
            }
        }
    }
    for (let stroke of strokes) {
        for (let point of stroke) {
            point[0] += (256 - maxX) / 2;
            point[1] += (256 - maxY) / 2;
        }
    }
}

function draw(canvasID, strokes, size=1.0) {
    const canvas = document.getElementById(canvasID);
    canvas.width = 256 * size;
    canvas.height = 256 * size;
    const ctx = canvas.getContext("2d");
    ctx.lineWidth = 3 * size;

    const delay = 10;
    let count = 0;

    ctx.beginPath();

    let timeout_count = 0;

    alignCenter(strokes);
    for (let stroke of strokes) {
        let firstPoint = stroke.shift();
        setTimeout((x, y) => {
            ctx.moveTo(x * size, y * size);
            timeout_count--;
        }, count++ * delay, firstPoint[0], firstPoint[1]);
        timeout_count++;

        for (let point of stroke) {
            setTimeout((x, y) => {
                ctx.lineTo(x * size, y * size);
                ctx.stroke();
                timeout_count--;

                if (timeout_count === 0) {
                    canvas.classList.add("ready");
                }
            }, count++ * delay, point[0], point[1]);
            timeout_count++;
        }
    }
}

// https://stackoverflow.com/a/111545/12123296
function encodeQueryData(data) {
   const ret = [];
   for (let d in data) {
       ret.push(encodeURIComponent(d) + "=" + encodeURIComponent(data[d]));
   }
   return ret.join("&");
}
