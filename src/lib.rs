use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyDict, PyList};
use pyo3::exceptions::PyValueError;
use scrypt::{scrypt, Params};
use aes_gcm::{
    aead::{Aead, KeyInit, OsRng, generic_array::GenericArray},
    Aes256Gcm, Nonce,
};
use rand::RngCore;
use std::fs::File;
use std::io::{Read, Write};
use std::os::unix::fs::PermissionsExt;
use std::path::Path;

const SCRYPT_LOG_N: u8 = 15; // 2^15 = 32768
const SCRYPT_R: u32 = 8;
const SCRYPT_P: u32 = 1;
const KEY_BYTES: usize = 32;
const NONCE_BYTES: usize = 12;
const SALT_BYTES: usize = 32;

fn derive_key_internal(password: &str, salt: &[u8]) -> Result<Vec<u8>, String> {
    let params = Params::new(SCRYPT_LOG_N, SCRYPT_R, SCRYPT_P, KEY_BYTES)
        .map_err(|e| format!("Invalid scrypt params: {}", e))?;
    let mut key = vec![0u8; KEY_BYTES];
    scrypt(password.as_bytes(), salt, &params, &mut key)
        .map_err(|e| format!("Scrypt failed: {}", e))?;
    Ok(key)
}

fn encrypt_internal(key: &[u8], plaintext: &[u8]) -> Result<Vec<u8>, String> {
    let aes_key = GenericArray::from_slice(key);
    let cipher = Aes256Gcm::new(aes_key);
    
    let mut nonce_bytes = [0u8; NONCE_BYTES];
    OsRng.fill_bytes(&mut nonce_bytes);
    let nonce = Nonce::from_slice(&nonce_bytes);
    
    let ciphertext = cipher.encrypt(nonce, plaintext)
        .map_err(|e| format!("Encryption failed: {}", e))?;
        
    let mut result = Vec::with_capacity(NONCE_BYTES + ciphertext.len());
    result.extend_from_slice(&nonce_bytes);
    result.extend_from_slice(&ciphertext);
    Ok(result)
}

fn decrypt_internal(key: &[u8], data: &[u8]) -> Result<Vec<u8>, String> {
    if data.len() < NONCE_BYTES {
        return Err("Data too short to contain nonce".to_string());
    }
    
    let nonce_bytes = &data[..NONCE_BYTES];
    let ciphertext = &data[NONCE_BYTES..];
    
    let aes_key = GenericArray::from_slice(key);
    let cipher = Aes256Gcm::new(aes_key);
    let nonce = Nonce::from_slice(nonce_bytes);
    
    cipher.decrypt(nonce, ciphertext)
        .map_err(|e| format!("Decryption failed: {}", e))
}

#[pyfunction]
fn derive_key<'py>(py: Python<'py>, password: &str, salt: &[u8]) -> PyResult<Bound<'py, PyBytes>> {
    let key = derive_key_internal(password, salt)
        .map_err(PyValueError::new_err)?;
    Ok(PyBytes::new_bound(py, &key))
}

#[pyfunction]
fn encrypt<'py>(py: Python<'py>, key: &[u8], plaintext: &[u8]) -> PyResult<Bound<'py, PyBytes>> {
    let result = encrypt_internal(key, plaintext)
        .map_err(PyValueError::new_err)?;
    Ok(PyBytes::new_bound(py, &result))
}

#[pyfunction]
fn decrypt<'py>(py: Python<'py>, key: &[u8], data: &[u8]) -> PyResult<Bound<'py, PyBytes>> {
    let plaintext = decrypt_internal(key, data)
        .map_err(PyValueError::new_err)?;
    Ok(PyBytes::new_bound(py, &plaintext))
}

#[pyfunction]
fn load_vault(py: Python, path: &str, password: &str) -> PyResult<PyObject> {
    if !Path::new(path).exists() {
        let dict = PyDict::new_bound(py);
        let list = PyList::empty_bound(py);
        dict.set_item("notes", list)?;
        return Ok(dict.into());
    }

    let mut file = File::open(path)?;
    let mut raw = Vec::new();
    file.read_to_end(&mut raw)?;

    if raw.len() < SALT_BYTES {
        return Err(PyValueError::new_err("File too small"));
    }

    let salt = &raw[..SALT_BYTES];
    let encrypted = &raw[SALT_BYTES..];

    let key = derive_key_internal(password, salt)
        .map_err(PyValueError::new_err)?;
    
    let plaintext = decrypt_internal(&key, encrypted)
        .map_err(|_| PyValueError::new_err("Wrong password or corrupted vault."))?;

    let text = std::str::from_utf8(&plaintext)
        .map_err(|e| PyValueError::new_err(format!("Invalid UTF-8: {}", e)))?;
        
    let json_module = py.import_bound("json")?;
    let parsed = json_module.call_method1("loads", (text,))?;
    
    Ok(parsed.into())
}

#[pyfunction]
fn save_vault(py: Python, path: &str, password: &str, vault: &Bound<'_, PyDict>) -> PyResult<()> {
    let json_module = py.import_bound("json")?;
    let json_dumps = json_module.getattr("dumps")?;
    
    let kwargs = PyDict::new_bound(py);
    kwargs.set_item("ensure_ascii", false)?;
    
    let text = json_dumps.call((vault,), Some(&kwargs))?.extract::<String>()?;
    let plaintext = text.as_bytes();

    let mut salt = vec![0u8; SALT_BYTES];
    OsRng.fill_bytes(&mut salt);

    let key = derive_key_internal(password, &salt)
        .map_err(PyValueError::new_err)?;
    let encrypted = encrypt_internal(&key, plaintext)
        .map_err(PyValueError::new_err)?;

    // Atomic write
    let target_path = Path::new(path);
    let parent = target_path.parent().unwrap_or(Path::new("."));
    
    let mut temp_file = tempfile::Builder::new()
        .prefix("tsunami-")
        .tempfile_in(parent)
        .map_err(|e| PyValueError::new_err(format!("Failed to create tempfile: {}", e)))?;
        
    // set permissions on the tempfile
    let mut perms = temp_file.as_file().metadata()?.permissions();
    perms.set_mode(0o600);
    temp_file.as_file().set_permissions(perms)?;

    temp_file.write_all(&salt)?;
    temp_file.write_all(&encrypted)?;
    temp_file.flush()?;
    
    temp_file.persist(path)
        .map_err(|e| PyValueError::new_err(format!("Failed to persist file: {}", e)))?;
        
    Ok(())
}

#[pymodule]
fn crypto(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(derive_key, m)?)?;
    m.add_function(wrap_pyfunction!(encrypt, m)?)?;
    m.add_function(wrap_pyfunction!(decrypt, m)?)?;
    m.add_function(wrap_pyfunction!(load_vault, m)?)?;
    m.add_function(wrap_pyfunction!(save_vault, m)?)?;
    Ok(())
}
