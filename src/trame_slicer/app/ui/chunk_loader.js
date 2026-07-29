const EXIT_SUCCESS = true;
const EXIT_FAILURE = false;

export async function load_files_by_chunks(files, inputs) {
  const trigger_name = inputs.trigger_name;
  const files_array = Array.from(files);
  if (files === undefined) {
    return {
      status: EXIT_FAILURE,
    };
  }

  let errorMsg = null;
  try {
    let maxSize = 10; // Mb
    let size = 0;
    let chunk = null;

    for (let offset = 0; offset < files.length; offset++) {
      if (chunk === null) {
        chunk = new DataTransfer();
      }
      chunk.items.add(files[offset]);
      size += files[offset].size;
      if (size > maxSize * 1e6) {
        await trame.trigger(trigger_name, [chunk.files]);
        chunk = null;
        size = 0;
      }
    }
  } catch (error) {
    errorMsg = error.toLocaleString();
  }
  await trame.trigger(trigger_name, [[]]); // Signal end of chunks, await loading

  return {
    status: errorMsg === null ? EXIT_SUCCESS : EXIT_FAILURE,
    errorMsg,
  };
}
