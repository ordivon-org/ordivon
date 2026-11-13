use crate::document::{CanonicalDocument, CanonicalValue};
use crate::error::CanonicalError;
use std::collections::BTreeMap;

/// Bounded native integer parser budget.
const MAX_INTEGER_DIGITS: usize = 4300;
pub(crate) const MAX_NESTING: usize = 995;

struct Parser<'a> {
    input: &'a str,
    position: usize,
}

impl<'a> Parser<'a> {
    fn remaining(&self) -> &'a str {
        &self.input[self.position..]
    }
    fn skip_whitespace(&mut self) {
        while let Some(&b' ' | &b'\n' | &b'\r' | &b'\t') = self.input.as_bytes().get(self.position)
        {
            self.position += 1;
        }
    }
    fn take(&mut self, expected: u8) -> bool {
        if self.input.as_bytes().get(self.position) == Some(&expected) {
            self.position += 1;
            true
        } else {
            false
        }
    }
    fn parse_string(&mut self) -> Result<String, CanonicalError> {
        if self.input.as_bytes().get(self.position) != Some(&b'"') {
            return Err(CanonicalError::InvalidJson);
        }
        let start = self.position;
        let mut at = start + 1;
        let bytes = self.input.as_bytes();
        while at < bytes.len() {
            match bytes[at] {
                b'\\' => at += 2,
                b'"' => {
                    let value = serde_json::from_str::<String>(&self.input[start..=at])
                        .map_err(|_| CanonicalError::InvalidJson)?;
                    self.position = at + 1;
                    return Ok(value);
                }
                _ => at += 1,
            }
        }
        Err(CanonicalError::InvalidJson)
    }
    fn parse_integer(&mut self) -> Result<CanonicalValue, CanonicalError> {
        let begin = self.position;
        self.take(b'-');
        let start_digits = self.position;
        if self.take(b'0') {
            if self
                .input
                .as_bytes()
                .get(self.position)
                .is_some_and(u8::is_ascii_digit)
            {
                return Err(CanonicalError::InvalidJson);
            }
        } else {
            match self.input.as_bytes().get(self.position) {
                Some(b'1'..=b'9') => {
                    self.position += 1;
                    while self
                        .input
                        .as_bytes()
                        .get(self.position)
                        .is_some_and(u8::is_ascii_digit)
                    {
                        self.position += 1;
                    }
                }
                _ => return Err(CanonicalError::InvalidJson),
            }
        }
        if self
            .input
            .as_bytes()
            .get(self.position)
            .is_some_and(|byte| matches!(byte, b'.' | b'e' | b'E'))
        {
            return Err(CanonicalError::NonIntegerNumber);
        }
        if self.position - start_digits > MAX_INTEGER_DIGITS {
            return Err(CanonicalError::IntegerDigitLimit);
        }
        let value = &self.input[begin..self.position];
        Ok(CanonicalValue::Integer(
            if value == "-0" { "0" } else { value }.to_owned(),
        ))
    }
    fn parse_value(&mut self, depth: usize) -> Result<CanonicalValue, CanonicalError> {
        if depth > MAX_NESTING {
            return Err(CanonicalError::ExcessiveNesting);
        }
        self.skip_whitespace();
        match self.input.as_bytes().get(self.position) {
            Some(b'n') if self.remaining().starts_with("null") => {
                self.position += 4;
                Ok(CanonicalValue::Null)
            }
            Some(b't') if self.remaining().starts_with("true") => {
                self.position += 4;
                Ok(CanonicalValue::Bool(true))
            }
            Some(b'f') if self.remaining().starts_with("false") => {
                self.position += 5;
                Ok(CanonicalValue::Bool(false))
            }
            Some(b'"') => self.parse_string().map(CanonicalValue::String),
            Some(b'[') => {
                self.position += 1;
                let mut values = Vec::new();
                self.skip_whitespace();
                if self.take(b']') {
                    return Ok(CanonicalValue::Array(values));
                }
                loop {
                    values.push(self.parse_value(depth + 1)?);
                    self.skip_whitespace();
                    if self.take(b']') {
                        break;
                    }
                    if !self.take(b',') {
                        return Err(CanonicalError::InvalidJson);
                    }
                }
                Ok(CanonicalValue::Array(values))
            }
            Some(b'{') => {
                self.position += 1;
                let mut entries = BTreeMap::new();
                self.skip_whitespace();
                if self.take(b'}') {
                    return Ok(CanonicalValue::Object(entries));
                }
                loop {
                    self.skip_whitespace();
                    let key = self.parse_string()?;
                    self.skip_whitespace();
                    if !self.take(b':') {
                        return Err(CanonicalError::InvalidJson);
                    }
                    let value = self.parse_value(depth + 1)?;
                    if entries.insert(key.clone(), value).is_some() {
                        return Err(CanonicalError::DuplicateKey(key));
                    }
                    self.skip_whitespace();
                    if self.take(b'}') {
                        break;
                    }
                    if !self.take(b',') {
                        return Err(CanonicalError::InvalidJson);
                    }
                }
                Ok(CanonicalValue::Object(entries))
            }
            Some(b'-' | b'0'..=b'9') => self.parse_integer(),
            _ => Err(CanonicalError::InvalidJson),
        }
    }
}

/// Decode the native canonical document, without floats or duplicate keys.
pub fn loads_strict(input: &str) -> Result<CanonicalDocument, CanonicalError> {
    let mut parser = Parser { input, position: 0 };
    let value = parser.parse_value(0)?;
    parser.skip_whitespace();
    if parser.position != input.len() {
        return Err(CanonicalError::InvalidJson);
    }
    Ok(CanonicalDocument(value))
}
